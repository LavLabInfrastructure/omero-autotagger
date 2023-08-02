from omero.gateway import RoiWrapper, ImageWrapper
def getRois(self):
    """
Gathers OMERO RoiI objects.

Parameters
----------
self: omero.gateway.ImageWrapper
    Omero Image object from conn.getObjects()
roi_service: omero.RoiService, optional
    Allows roiservice passthrough for performance
    """
    roi_service = self._conn.getRoiService()

    result = roi_service.findByImage(self.getId(), None, self._conn.SERVICE_OPTS)
    rv = []
    if result.rois:
        for roi in result.rois:
            rv.append(RoiWrapper(self._conn, roi))
    
    roi_service.close()
    return rv

if not hasattr(ImageWrapper, 'getROIs'):
    ImageWrapper.getRois = getRois

