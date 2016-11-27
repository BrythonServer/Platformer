# Exemplar implementation of the Platformer Project

from ggame import App, Sprite, RectangleAsset, LineStyle, Color
   
# A super wall class for wall-ish behaviors
class GenericWall(Sprite):
    def __init__(self, x, y, w, h, color):
        snapfunc = lambda X : X - X % w
        super().__init__(
            RectangleAsset(w,h,LineStyle(0,Color(0, 1.0)), color),
            (snapfunc(x), snapfunc(y)))
        # destroy any overlapping walls
        collideswith = self.collidingWithSprites(GenericWall)
        if len(collideswith):
            collideswith[0].destroy()

# impenetrable wall (black)
class Wall(GenericWall):
    def __init__(self, x, y):
        super().__init__(x, y, 50, 50, Color(0, 1.0))

# pass thru going up wall
class Platform(GenericWall):
    def __init__(self, x, y):
        super().__init__(x, y, 50, 15, Color(0xff0000, 1.0))
    
# super class for anything that falls and lands or bumps into walls
class GravityActor(Sprite):
    def __init__(self, x, y, width, height, color, app):
        self.vx = self.vy = 0
        self.stuck = False
        self.app = app                          # app, need to know
        self.resting = False                    # whether resting on wall
        super().__init__(
            RectangleAsset(
                width, height, 
                LineStyle(0, Color(0, 1.0)),
                color),
            (x, y)) 
        # destroy self if overlapping with anything
        collideswith = self.collidingWithSprites()
        if len(collideswith):
            self.destroy()
        
    def step(self):
        # then process movement in vertical direction
        self.y += self.vy
        collides = self.collidingWithSprites(Wall)
        collides.extend(self.collidingWithSprites(Platform))
        for collider in collides:
            if self.vy > 0 or self.vy < 0:
                if self.vy > 0:
                    self.y = collider.y - self.height - 1
                    self.resting = True
                    self.vy = 0
                # upward collisions for true Wall only
                elif isinstance(collider, Wall):
                    self.y = collider.y + collider.height
                    self.vy = 0
        # process movement in horizontal direction first
        self.x += self.vx
        collides = self.collidingWithSprites(Wall)
        collides.extend(self.collidingWithSprites(Platform))
        for collider in collides:
            if self.vx > 0 or self.vx < 0:
                if self.vx > 0:
                    self.x = collider.x - self.width
                else:
                    self.x = collider.x + collider.width
                self.vx = 0
        # adjust vertical velocity for acceleration due to gravity
        self.vy += 1
        # check for out of bounds
        if self.y > self.app.height:
            self.app.killMe(self)

# "bullets" to fire from Turrets.
class Bolt(Sprite):
    def __init__(self, direction, x, y, app):
        w = 15
        h = 5
        self.direction = direction
        self.app = app
        super().__init__(RectangleAsset(w, h, Color(0x00ffff)),(x-w//2, y-h//2))

    def step(self):
        self.x += self.direction
        # check for out of bounds
        if self.x > self.app.width or self.x < 0:
            self.app.killMe(self)
        # check for any collisions
        hits = self.collidingWithSprites()
        selfdestruct = False
        for target in hits:
            # destroy players and other bolts
            if isinstance(target, Player) or isinstance(target, Bolt):
                self.app.killMe(target)
            # self destruct on anything but a Turret
            if not isinstance(target, Turret):
                selfdestruct = True
        if selfdestruct:
            self.app.killMe(self)


# An object that generates bolts (laser shots)
class Turret(GravityActor):
    def __init__(self, x, y, app):
        w = 20
        h = 35
        r = 10
        self.time = 0
        self.direction = 1
        super().__init__(x-w//2, y-h//2, w, h, Color(0xff8800, 1.0), app)
        
    def step(self):
        super().step()
        self.time += 1
        if self.time % 100 == 0:
            Bolt(self.direction, 
                 self.x+self.rect.width//2,
                 self.y+10,
                 self.app)
            self.direction *= -1

        

# The player class. only one instance of this is allowed.
class Player(GravityActor):
    def __init__(self, x, y, app):
        w = 15
        h = 30
        super().__init__(x-w//2, y-h//2, w, h, Color(0x00ff00, 1.0), app)

    def step(self):
        # look for spring collisions
        springs = self.collidingWithSprites(Spring)
        if len(springs):
            self.vy = -15
            self.resting = False
                # check for out of bounds
        super().step()
        
    def move(self, key):
        if key == "left arrow":
            if self.vx > 0:
                self.vx = 0
            else:
                self.vx = -5
        elif key == "right arrow":
            if self.vx < 0:
                self.vx = 0
            else:
                self.vx = 5
        elif key == "up arrow" and self.resting:
            self.vy = -10
            self.resting = False
            
    def stopMove(self, key):
        if key == "left arrow" or key == "right arrow":
            self.vx = 0

  
# A spring makes the player "bounce" higher than she can jump
class Spring(GravityActor):
    def __init__(self, x, y, app):
        w = 10
        h = 4
        super().__init__(x-w//2, y-h//2, w, h, Color(0x0000ff, 1.0), app)
        
    def step(self):
        if self.resting:
            self.app.FallingSprings.remove(self)
        super().step()

# The application class. Subclass of App
class Platformer(App):
    def __init__(self):
        super().__init__()
        self.p = None
        self.pos = (0,0)
        self.listenKeyEvent("keydown", "w", self.newWall)
        self.listenKeyEvent("keydown", "p", self.newPlayer)
        self.listenKeyEvent("keydown", "s", self.newSpring)
        self.listenKeyEvent("keydown", "f", self.newFloor)
        self.listenKeyEvent("keydown", "l", self.newLaser)
        self.listenKeyEvent("keydown", "left arrow", self.moveKey)
        self.listenKeyEvent("keydown", "right arrow", self.moveKey)
        self.listenKeyEvent("keydown", "up arrow", self.moveKey)
        self.listenKeyEvent("keyup", "left arrow", self.stopMoveKey)
        self.listenKeyEvent("keyup", "right arrow", self.stopMoveKey)
        self.listenKeyEvent("keyup", "up arrow", self.stopMoveKey)
        self.listenMouseEvent("mousemove", self.moveMouse)
        self.FallingSprings = []
        self.KillList = []

    def moveMouse(self, event):
        self.pos = (event.x, event.y)
    
    def newWall(self, event):
        Wall(self.pos[0], self.pos[1])
        
    def newPlayer(self, event):
        for p in Platformer.getSpritesbyClass(Player):
            p.destroy()
            self.p = None
        self.p = Player(self.pos[0], self.pos[1], self)
    
    def newSpring(self, event):
        print("new spring")
        self.FallingSprings.append(Spring(self.pos[0], self.pos[1], self))
    
    def newFloor(self, event):
        Platform(self.pos[0], self.pos[1])
        
    def newLaser(self, event):
        Turret(self.pos[0], self.pos[1], self)
        
    def moveKey(self, event):
        if self.p:
            self.p.move(event.key)
        
    def stopMoveKey(self, event):
        if self.p:
            self.p.stopMove(event.key)
        
    def step(self):
        if self.p:
            self.p.step()
        for s in self.FallingSprings:
            s.step()
            """
        for t in Platformer.getSpritesbyClass(Turret):
            t.step()
        for b in Platformer.getSpritesbyClass(Bolt):
            b.step()
            """
        for k in self.KillList:
            k.destroy()
        self.KillList = []
            
    def killMe(self, obj):
        print("killing ", obj)
        if obj in self.FallingSprings:
            self.FallingSprings.remove(obj)
        elif obj == self.p:
            self.p = None
        self.KillList.append(obj)
        
# Execute the application by instantiate and run        
app = Platformer()
app.run()
