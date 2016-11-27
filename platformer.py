# Exemplar implementation of the Platformer Project

from ggame import App, Sprite
   
# A super wall class for wall-ish behaviors
class GenericWall(Actor):
    def __init__(self, x, y, w, h, color, actor_list):
        snapfunc = lambda X : X - X % w
        super().__init__(snapfunc(x), snapfunc(y), 
                         w, h, actor_list)
        self.color = color
        self.draw()
        # destroy any overlapping walls
        collideswith = self.overlapping_actors(GenericWall)
        if len(collideswith):
            collideswith[0].destroy()
        
    def draw(self):
        pygame.draw.rect(self.image, self.color, self.image.get_rect())
        self.dirty = 1

# impenetrable wall (black)
class Wall(GenericWall):
    def __init__(self, x, y, actor_list):
        super().__init__(x, y, 50, 50, 
                         pygame.Color('black'), actor_list)   
             
# pass thru going up wall
class Platform(GenericWall):
    def __init__(self, x, y, actor_list):
        super().__init__(x, y, 50, 15, 
                         pygame.Color('red'), actor_list)
    
# super class for anything that falls and lands or bumps into walls
class GravityActor(Actor):
    def __init__(self, x, y, width, height, actor_list, app):
        self.vx = self.vy = 0
        self.stuck = False
        self.color = pygame.Color('black')
        self.app = app                          # app, need to know
        self.sitting = False                    # whether resting on wall
        super().__init__(x, y, width, height, actor_list)
        # destroy self if overlapping with anything
        collideswith = self.overlapping_actors()
        if len(collideswith):
            self.destroy()
        
    def update(self):
        # note the original position
        oldpos = self.rect.copy()
        # process movement in horizontal direction first
        self.x += self.vx
        collides = self.overlapping_actors(GenericWall)
        for collider in collides:
            if self.vx > 0 or self.vx < 0:
                if self.vx > 0:
                    self.x = collider.x - self.width
                else:
                    self.x = collider.x + collider.width
                self.vx = 0
        # then process movement in vertical direction
        self.y += self.vy
        collides = self.overlapping_actors(GenericWall)
        for collider in collides:
            if self.vy > 0 or self.vy < 0:
                if self.vy > 0:
                    self.y = collider.y - self.height
                    self.resting = True
                    self.vy = 0
                # upward collisions for true Wall only
                elif isinstance(collider, Wall):
                    self.y = collider.y + collider.height
                    self.vy = 0
        # adjust vertical velocity for acceleration due to gravity
        self.vy += 1
        # check for out of bounds
        if self.y > self.app.screensize[1]:
            self.destroy()
        # only dirty if we moved
        if oldpos != self.rect:
            self.dirty = 1

    def draw(self):
        pygame.draw.rect(self.image, self.color, self.image.get_rect())
        self.dirty = 1

# "bullets" to fire from Turrets.
class Bolt(Actor):
    def __init__(self, direction, x, y, actor_list, app):
        w = 15
        h = 5
        self.direction = direction
        self.app = app
        super().__init__(x-w//2, y-h//2, w, h, actor_list)
    
    def update(self):
        self.rect.x += self.direction
        self.dirty = 1
        # check for out of bounds
        if self.x > self.app.screensize[1] or self.x < 0:
            self.destroy()
        # check for any collisions
        hits = self.overlapping_actors()
        selfdestruct = False
        for target in hits:
            # destroy players and other bolts
            if isinstance(target, Player) or isinstance(target, Bolt):
                target.destroy()
            # self destruct on anything but a Turret
            if not isinstance(target, Turret):
                selfdestruct = True
        if selfdestruct:
            self.destroy()
            
    def draw(self):
        pygame.draw.rect(self.image, pygame.Color('purple'), self.image.get_rect())
        self.dirty = 1

# An object that generates bolts (laser shots)
class Turret(GravityActor):
    def __init__(self, x, y, actor_list, app):
        w = 20
        h = 35
        r = 10
        self.time = 0
        self.direction = 1
        self.body = pygame.Rect((0,2*r,w,h-2*r))
        super().__init__(x-w//2, y-h//2, w, h, actor_list, app)
        
    def update(self):
        super().update()
        self.time += 1
        if self.time % 100 == 0:
            Bolt(self.direction, 
                 self.x+self.rect.width//2,
                 self.y+10,
                 self.actors,
                 self.app)
            self.direction *= -1
        
    def draw(self):
        color = pygame.Color('orange')
        pygame.draw.rect(self.image, color, self.body)
        pygame.draw.circle(self.image, color, (10,10), 10)
        self.dirty = 1

# The player class. only one instance of this is allowed.
class Player(GravityActor):
    def __init__(self, x, y, actor_list, app):
        w = 15
        h = 30
        super().__init__(x-w//2, y-h//2, w, h, actor_list, app)
        self.color = pygame.Color('green')
        self.draw()
        
    def update(self):
        # look for spring collisions
        springs = self.overlapping_actors(Spring)
        if len(springs):
            self.vy = -15
            self.resting = False
        super().update()
        
    def move(self, key):
        if key == K_LEFT:
            if self.vx > 0:
                self.vx = 0
            else:
                self.vx = -5
        elif key == K_RIGHT:
            if self.vx < 0:
                self.vx = 0
            else:
                self.vx = 5
        elif key == K_UP and self.resting:
            self.vy = -10
            self.resting = False
        
# A spring makes the player "bounce" higher than she can jump
class Spring(GravityActor):
    def __init__(self, x, y, actor_list, app):
        w = 10
        h = 4
        super().__init__(x-w//2, y-h//2, w, h, actor_list, app)
        self.color = pygame.Color('blue')
        self.draw()
        
     
# The application class. Subclass of PygameApp
class Platformer(PygameApp):
    def __init__(self):
        super().__init__(screensize=(800,800), fullscreen=False)
        self.setbackgroundcolor(pygame.Color('white'))
        # pygame.key.set_repeat(10)              # allow keys to repeat when held 10 msec
        self.p = None
        
    def handle_event(self, event):
        pos = pygame.mouse.get_pos()
        if event.type == KEYDOWN:
            if event.key == K_q:
                return False
            # Build some wall
            elif event.key == K_w:
                Wall(pos[0], pos[1], self.spritegroup)
            # Create a player
            elif event.key == K_p:
                if self.p:
                    self.p.destroy()
                self.p = Player(pos[0], pos[1], self.spritegroup, self)
            # Create a spring
            elif event.key == K_s:
                Spring(pos[0], pos[1], self.spritegroup, self)
            # Create a platform (floor)
            elif event.key == K_f:
                Platform(pos[0], pos[1], self.spritegroup)
            # Create a laser turret
            elif event.key == K_l:
                Turret(pos[0], pos[1], self.spritegroup, self)
            # Handle player movements
            elif event.key in (K_UP, K_LEFT, K_RIGHT):
                self.p.move(event.key)
        return True


        
# Execute the application by instantiate and run        
app = Platformer()
app.run()
