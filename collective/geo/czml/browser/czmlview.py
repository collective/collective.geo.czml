from zope.interface import implements, Interface
from zope.component import getUtility

try:
    from shapely.geometry import asShape
except:
    from pygeoif.geometry import as_shape as asShape

import czml

from Products.Five import BrowserView

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.Expression import Expression, getExprContext

from plone.registry.interfaces import IRegistry

from collective.geo.geographer.interfaces import IGeoreferenced
from collective.geo.settings.interfaces import IGeoFeatureStyle

def get_marker_image(context, marker_img):
    try:
        marker_img = Expression(str(marker_img))(getExprContext(context))
    except:
        marker_img = ''
    return marker_img



class ICzmlDocument(Interface):
    ''' Marker Interface '''


class CzmlBaseDocument(BrowserView):
    implements(ICzmlDocument)

    defaultstyles = None
    styles = None

    def __init__(self, context, request):
        self.context = context
        self.request = request
        registry = getUtility(IRegistry)
        self.defaultstyles = registry.forInterface(IGeoFeatureStyle)

    @property
    def portal(self):
        return getToolByName(self.context, 'portal_url').getPortalObject()

    def _get_style(self):
        def to_dict(rp):
            styled = {}
            for k in rp.__schema__.names():
                styled[k] = getattr(rp, k)
            return styled
        style= {}
        if not self.styles:
            styles = to_dict(self.defaultstyles)
        else:
            if self.styles['use_custom_styles']:
                styles = self.styles
            else:
                styles = to_dict(self.defaultstyles)
        style['fill'] = czml.hexcolor_to_rgba(styles['polygoncolor'])
        style['stroke'] = czml.hexcolor_to_rgba(styles['linecolor'])
        style['width'] = styles['linewidth']
        img = get_marker_image( self.context,
                    styles['marker_image'])
        style['image']= img
        style['scale'] = styles['marker_image_size']
        return style

    @property
    def portal_catalog(self):
        return getToolByName(self.context, 'portal_catalog')


class CzmlDocument(CzmlBaseDocument):

    def __call__(self):
        self.request.RESPONSE.setHeader('Content-Type','application/json; charset=utf-8')
        try:
            geometry = IGeoreferenced(self.context)
        except:
            return '[]'
        try:
            self.styles = IGeoFeatureStyle(self.context).geostyles
        except:
            self.styles = None
        import ipdb; ipdb.set_trace()
        classes = geometry.geo['type'].lower() + ' '
        classes += self.context.getPhysicalPath()[-2].replace('.','-') #+ ' '
        json_result = [
                geojson.Feature(
                    id=self.context.id.replace('.','-'),
                    geometry=geometry.geo,
                    properties={
                        "title": self.context.Title(),
                        "description": self.context.Description(),
                        "style": self._get_style(geometry.geo),
                        "url": self.context.absolute_url(),
                        "classes" : classes,
                        })]
        return geojson.dumps(geojson.FeatureCollection(json_result))

class CzmlFolderDocument(CzmlBaseDocument):

    def get_brains(self):
        return self.context.getFolderContents()

    def __call__(self):
        json_result = czml.CZML()
        for brain in self.get_brains():
            if brain.zgeo_geometry:
                self.styles = brain.collective_geo_styles
                geom = { 'type': brain.zgeo_geometry['type'],
                            'coordinates': brain.zgeo_geometry['coordinates']}
                if geom['coordinates']:
                    style = self._get_style()
                    packet = czml.CZMLPacket(id=brain.UID)
                    if geom['type'] == 'Point':
                        label = czml.Label()
                        label.text = brain.Title.decode('UTF-8')
                        label.show = True
                        packet.label = label
                        if style['image']:
                            billboard = czml.Billboard()
                            billboard.image = style['image']
                            billboard.scale = style['scale']
                            billboard.show = True
                            packet.billboard = billboard
                        else:
                            point = czml.Point()
                            point.color = {'rgba': style['fill']}
                            point.outlineColor = {'rgba': style['stroke']}
                            point.pixelSize = 20 * style['scale']
                            point.outlineWidth = style['width']
                            point.show = True
                            packet.point = point
                        position = czml.Position()
                        position.cartographicDegrees = geom
                        packet.position = position
                    elif geom['type'] == 'LineString':
                        pl = czml.Polyline()
                        pl.color = {'rgba': style['fill']}
                        pl.outlineColor = {'rgba': style['stroke']}
                        pl.width = style['width'] * style['scale']
                        pl.outlineWidth = style['width']
                        pl.show = True
                        v = czml.VertexPositions()
                        v.cartographicDegrees = geom
                        packet.vertexPositions = v
                        packet.polyline = pl
                    json_result.append(packet)

        self.request.RESPONSE.setHeader('Content-Type','application/json; charset=utf-8')
        return json_result.dumps()

class CzmlTopicDocument(CzmlFolderDocument):

    def get_brains(self):
        return self.context.queryCatalog()
