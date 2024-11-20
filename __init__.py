# -*- coding: utf-8 -*-
"""
/***************************************************************************
 StreckenkmFinder
                                 A QGIS plugin
 Klicke auf eine Karte und erhalte den nähsten Streckenkm
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-11-15
        copyright            : (C) 2024 by Christoph Mellüh
        email                : christoph.mellueh@deutschebahn.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
import os

__version__ = "0.1.2"
# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load StreckenkmFinder class from file StreckenkmFinder.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .DB_Streckenkm import StreckenkmFinder
    return StreckenkmFinder(iface)

def get_icon_path(icon_name = None):
    if icon_name is None:
        icon_name = "icon.png"
    return os.path.join(os.path.dirname(__file__),"icons", icon_name)

if __name__ == "__main__":
    pass