import pygame
import pytmx
import pyscroll

from screen import Screen

class Map:

    def __init__(self,screen : Screen):
        self.screen = screen
        self.tmx_data = pytmx.load_pygame(f"./assets/map/background.tmx")
        self.map_layer = pyscroll.BufferedRenderer(pyscroll.data.TiledMapData(self.tmx_data), self.screen.get_size())
        self.group = pyscroll.PyscrollGroup(map_layer=self.map_layer,default_layer=7)
        self.map_layer.zoom = 2

    def  add_player(self,player):
        self.group.add(player)

    def update(self):
        self.group.update()
        self.group.draw(self.screen.get_display())