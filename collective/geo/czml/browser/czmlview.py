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

    def normalize_color(self, color):
        if color:
            if color.startswith('#'):
                color = color[1:]
            if len(color)==3 or len(color)==4:
                color =''.join([b*2 for b in color])
            if len(color)==6:
                color = color +'3c'
            if len(color)==8:
                return color.upper()
        return 'AABBCCDD'

    def _get_style(self, geo_type):
        style= {}
        if self.styles:
            fill = self.normalize_color(self.styles['polygoncolor'])
            stroke = self.normalize_color(self.styles['linecolor'])
            if self.styles['use_custom_styles']:
                if geo_type['type'].endswith('Polygon'):
                    style['fill'] = fill
                    style['stroke'] = stroke
                    style['width'] = self.styles['linewidth']
                elif geo_type['type'].endswith('LineString'):
                    style['stroke'] = stroke
                    style['width'] = self.styles['linewidth']
                elif geo_type['type'].endswith('Point'):
                    img = self.styles['marker_image']
                    style['fill'] = fill
                    style['stroke'] =stroke
                    style['width'] = self.styles['linewidth']
                    if img.startswith('string:${portal_url}'):
                        img = self.portal.absolute_url() + img[20:]
                    style['image']= img
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
                    packet = czml.CZMLPacket(id=brain.UID)
                    label = czml.Label()
                    label.text = brain.Title.decode('UTF-8')
                    label.show = False
                    packet.label = label
                    if geom['type'] == 'Point':
                        #if self.styles.get('use_custom_styles', False):
                        billboard = czml.Billboard()
                        billboard.image = get_marker_image(
                            self.context, self.styles['marker_image'])
                        billboard.scale = self.styles['marker_image_size']
                        billboard.show = True
                        packet.billboard = billboard
                        #else:
                        #    pass #XXX use Point here
                        position = czml.Position()
                        position.cartesian = geom
                        packet.position = position

                    json_result.append(packet)

        self.request.RESPONSE.setHeader('Content-Type','application/json; charset=utf-8')
        return json_result.dumps()

class CzmlTopicDocument(CzmlFolderDocument):

    def get_brains(self):
        return self.context.queryCatalog()
