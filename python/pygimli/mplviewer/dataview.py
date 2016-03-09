#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Some data related viewer
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize
from matplotlib.patches import Rectangle
from matplotlib.collections import PatchCollection
import pygimli as pg
from pygimli.mplviewer import updateAxes as updateAxes_


def generateMatrix(xvec, yvec, vals, full=False):
    """ generate a data matrix from x/y and value vectors

    Parameters
    ----------
    xvec, yvec, vals : iterables (list, np.array, pg.RVector) of same length

    full: bool [False]
        generate a fully symmetric matrix containing all unique xvec+yvec
        otherwise A is squeezed to the individual unique vectors

    Returns
    -------
    A : np.ndarray(2d)
        matrix containing the values sorted according to unique xvec/yvec
    xmap/ymap : dict {key: num}
        dictionaries for accessing matrix position (row/col number from x/y[i])
    """
    if full:
        xymap = {xy: ii for ii, xy in enumerate(np.unique(np.hstack((xvec,
                                                                     yvec))))}
        xmap = xymap
        ymap = xymap
    else:
        xmap = {xx: ii for ii, xx in enumerate(np.unique(xvec))}
        ymap = {yy: ii for ii, yy in enumerate(np.unique(yvec))}
    A = np.zeros((len(ymap), len(xmap)))
    inot = []
    nshow = min([len(xvec), len(yvec), len(vals)])
    for i in range(nshow):
        xi, yi = xvec[i], yvec[i]
        if A[ymap[yi], xmap[xi]]:
            inot.append(i)
        A[ymap[yi], xmap[xi]] = vals[i]
    if len(inot) > 0:
        print(len(inot), "data of", nshow, "not shown")
        if len(inot) < 30:
            print(inot)
    return A, xmap, ymap


def patchMatrix(A, xmap=None, ymap=None, ax=None, cMin=None, cMax=None,
                logScale=None, label=None, dx=1, **kwargs):
    """ plot previously generated (generateVecMatrix) matrix

    Parameters
    ----------
    A : numpy.array2d
        matrix to show
    xmap : dict {i:num}
        dict (must match A.shape[0])
    ymap : iterable
        vector for x axis (must match A.shape[0])
    ax : mpl.axis
        axis to plot, if not given a new figure is created
    cMin/cMax : float
        minimum/maximum color values
    logScale : bool
        logarithmic colour scale [min(A)>0]
    label : string
        colorbar label
    """
    mat = np.ma.masked_where(A == 0.0, A, False)
    if cMin is None:
        cMin = np.min(mat)
    if cMax is None:
        cMax = np.max(mat)
    if logScale is None:
        logScale = (cMin > 0.0)
    if logScale:
        norm = LogNorm(vmin=cMin, vmax=cMax)
    else:
        norm = Normalize(vmin=cMin, vmax=cMax)
    if 'ax' is None:
        fig, ax = plt.subplots()

    iy, ix = np.nonzero(A != 0)
    recs = []
    vals = []
    for i in range(len(ix)):
        recs.append(Rectangle((ix[i]-dx/2, iy[i]-0.5), dx, 1))
        vals.append(A[iy[i], ix[i]])

    pp = PatchCollection(recs)
    col = ax.add_collection(pp)
    pp.set_edgecolor(None)
    pp.set_linewidths(0.0)
    if 'cmap' in kwargs:
        pp.set_cmap(kwargs.pop('cmap'))
    pp.set_norm(norm)
    pp.set_array(np.array(vals))
    pp.set_clim(cMin, cMax)

    updateAxes_(ax)
    cbar = None
    if kwargs.pop('colorBar', True):
        cbar = pg.mplviewer.createColorbar(col, cMin=cMin, cMax=cMax, nLevs=5,
                                           label=label)
    return ax, cbar


def plotMatrix(A, xmap=None, ymap=None, ax=None, cMin=None, cMax=None,
               logScale=None, label=None, **kwargs):
    """ Plot previously generated (generateVecMatrix) matrix

    Parameters
    ----------
    A : numpy.array2d
        matrix to show
    xmap : dict {i:num}
        dict (must match A.shape[0])
    ymap : iterable
        vector for x axis (must match A.shape[0])
    ax : mpl.axis
        axis to plot, if not given a new figure is created
    cMin/cMax : float
        minimum/maximum color values
    logScale : bool
        logarithmic colour scale [min(A)>0]
    label : string
        colorbar label
    """
    if xmap is None:
        xmap = {i: i for i in range(A.shape[0])}
    if ymap is None:
        ymap = {i: i for i in range(A.shape[1])}
    mat = np.ma.masked_where(A == 0.0, A, False)
    if cMin is None:
        cMin = np.min(mat)
    if cMax is None:
        cMax = np.max(mat)
    if logScale is None:
        logScale = (cMin > 0.0)
    if logScale:
        norm = LogNorm(vmin=cMin, vmax=cMax)
    else:
        norm = Normalize(vmin=cMin, vmax=cMax)
    if ax is None:
        fig, ax = plt.subplots()

    im = ax.imshow(mat, norm=norm, interpolation='nearest')
    if 'cmap' in kwargs:
        im.set_cmap(kwargs.pop('cmap'))
    ax.set_aspect(kwargs.pop('aspect', 1))
    cbar = None
    if kwargs.pop('colorBar', True):
        cbar = pg.mplviewer.createColorbar(im, cMin=cMin, cMax=cMax, nLevs=5,
                                           label=label)
    ax.grid(True)
    xt = np.unique(ax.get_xticks().clip(0, len(xmap)-1))
    yt = np.unique(ax.get_xticks().clip(0, len(ymap)-1))

    if kwargs.pop('showally', False):
        yt = np.arange(len(ymap))
    else:
        yt = np.round(np.linspace(0, len(ymap)-1, 5))
#    print(yt)

    xx = np.sort([k for k in xmap])
    ax.set_xticks(xt)
    ax.set_xticklabels(['{:g}'.format(round(xx[int(ti)], 2)) for ti in xt])
    yy = np.unique([k for k in ymap])
    ax.set_yticks(yt)
    ax.set_yticklabels(['{:g}'.format(round(yy[int(ti)], 2)) for ti in yt])
#    ax.set_yticklabels(['{:g}'.format(round(yy[int(ti)], 2)) for ti in yt])
    return ax, cbar


def plotVecMatrix(xvec, yvec, vals, full=False, **kwargs):
    """Plot three vectors as matrix.

    Parameters
    ----------
    xvec, yvec : iterable (e.g. list, np.array, pg.RVector) of identical length
        vectors defining the indices into the matrix
    vals : iterable of same length as xvec/yvec
        vector containing the values to show
    full: bool [False]
        use a fully symmetric matrix containing all unique xvec+yvec
        otherwise A is squeezed to the individual unique xvec/yvec values

    **kwargs: forwarded to plotMatrix
        *   ax : mpl.axis
            Axis to plot, if not given a new figure is created
        * cMin/cMax : float
            Minimum/maximum color values
        * logScale : bool
            Lgarithmic colour scale [min(A)>0]
        * label : string
            Colorbar label
    """
    A, xmap, ymap = generateMatrix(xvec, yvec, vals, full)
    return plotMatrix(A, xmap, ymap, **kwargs)


def plotDataContainerAsMatrix(data, x=None, y=None, v=None, **kwargs):
    """ plot data container as matrix

    for each x, y and v token strings or vectors should be given
    """
    if isinstance(x, str):
        x = data(x)
    if isinstance(y, str):
        y = data(y)
    if isinstance(v, str):
        v = data(v)
    if x is None or y is None or v is None:
        raise Exception("Vectors or strings must be given")
    if len(x) != len(y) or len(x) != len(v):
        raise Exception("lengths x/y/v not matching: {:d}!={:d}!={:d}".format(
            len(x), len(y), len(v)))
    return plotVecMatrix(x, y, v, **kwargs)


def drawSensorAsMarker(ax, data):
    """
        Draw Sensor marker, these marker are pickable
    """
    elecsX = []
    elecsY = []

    for i in range(len(data.sensorPositions())):
        elecsX.append(data.sensorPositions()[i][0])
        elecsY.append(data.sensorPositions()[i][1])

    electrodeMarker, =  ax.plot(elecsX, elecsY, 'x', color='black', picker=5.)

    ax.set_xlim([data.sensorPositions()[0][0] - 1.,
                 data.sensorPositions()[data.sensorCount() - 1][0] + 1.])

    return electrodeMarker


def drawTravelTimeData(a, data):
    """
        Draw first arrival traveltime data into mpl axes a.
        data of type \ref DataContainer must contain sensorIdx 's' and 'g'
        and thus being numbered internally [0..n)
    """

    x = pg.x(data.sensorPositions())
#    z = pg.z(data.sensorPositions())

    shots = pg.unique(pg.sort(data('s')))
    geoph = pg.unique(pg.sort(data('g')))

    startOffsetIDX = 0

    if min(min(shots), min(geoph)) == 1:
        startOffsetIDX = 1

    a.set_xlim([min(x), max(x)])
    a.set_ylim([max(data('t')), -0.002])
    a.figure.show()

    for shot in shots:
        gIdx = pg.find(data('s') == shot)
        sensorIdx = [int(i__ - startOffsetIDX) for i__ in data('g')[gIdx]]
        a.plot(x[sensorIdx], data('t')[gIdx], 'x-')

    yPixel = a.transData.inverted().transform_point((1, 1))[1] - \
        a.transData.inverted().transform_point((0, 0))[1]
    xPixel = a.transData.inverted().transform_point((1, 1))[0] - \
        a.transData.inverted().transform_point((0, 0))[0]

    # draw shot points
    a.plot(x[[int(i__ - startOffsetIDX) for i__ in shots]],
           np.zeros(len(shots)) + 8. * yPixel, 'gv', markersize=8)

    # draw geophone points
    a.plot(x[[int(i__ - startOffsetIDX) for i__ in geoph]],
           np.zeros(len(geoph)) + 3. * yPixel, 'r^', markersize=8)

    a.grid()
    a.set_ylim([max(data('t')), +16. * yPixel])
    a.set_xlim([min(x) - 5. * xPixel, max(x) + 5. * xPixel])

    a.set_xlabel('x-Coordinate [m]')
    a.set_ylabel('Traveltime [ms]')
# def drawTravelTimeData(...)
