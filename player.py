# Holds the player pacman

# Imports
from graphics import *
import time
import config
from boundingbox import *
import math
from food import *
import threading

# Import win sound, or try to, if failed dont use it
soundEnabled = True
try:
    import winsound
except:
    soundEnabled = False

# Class defintion
class Player:
    def __init__(self, window, world, winCallback, size = 39.5):
        # Starting positions
        startX = config.WINDOW_WIDTH / 2 - 15
        startY = 525

        # Initialize variables
        self.box = Rectangle(Point(0, 0), Point(size, size))
        self.boundingBox = BoundingBox(Point(startX, startY), Point(size, size))
        self.projectedBox = BoundingBox(Point(startX, startY), Point(size, size))
        self.direction = "n"
        self.nextDirection = "n"
        self.movmentSpeed = 1
        self.score = 0
        self.life = 3 # Player has 3 lifes
        self.alive = False
        self.lastScared = 0
        self.collided = False
        self.ghostCount = 1

        # Initialize life images
        self.lifeImages = [Image(Point(60, config.WINDOW_HEIGHT - 20), "images/directions/westFirst.png"),
                           Image(Point(100, config.WINDOW_HEIGHT - 20), "images/directions/westFirst.png"),
                           Image(Point(140, config.WINDOW_HEIGHT - 20), "images/directions/westFirst.png")]
        for i in self.lifeImages:
            i.draw(window)

        # Initialize food list
        self.foodlist = []
        self.derenderingFood = []

        for square in world.squares:
            f2 = None

            f2 = Food(square.pos.getX(), square.pos.getY(), "yellow", "blue", square.type, window)

            self.foodlist.append(f2)

        # Animation variables
        self.images = (Image(Point(0, 0), "images/directions/center.png"),
                       Image(Point(0, 0), "images/directions/northFirst.png"),
                       Image(Point(0, 0), "images/directions/southFirst.png"),
                       Image(Point(0, 0), "images/directions/eastFirst.png"),
                       Image(Point(0, 0), "images/directions/westFirst.png"))
        self.frame = 0 # Holds the frame, if its facing a direction or center
        self.animationDelay = 0.1
        self.lastFrameTime = time.time()

        # Move graphics box and setfill
        self.box.move(startX, startY)
        for p in self.images:
            p.move(startX + size / 2, startY + size / 2)

        self.winCallback = winCallback

    def draw(self, window):
        """Draws player to the screen"""
        self.box.draw(window)

    def move(self, direction):
        """Moves player direction"""
        # Get projection position and see if it collides
        self.nextDirection = direction

    def respawn(self):
        """Respawns the player"""
        self.alive = False
        toPos = Point((config.WINDOW_WIDTH / 2 - 15) - self.boundingBox.pos.getX(), (525 - self.boundingBox.pos.getY()))
        self.boundingBox.move(toPos.getX(), toPos.getY())
        self.direction = "n"
        self.nextDirection = "n"

    def update(self, world, ghosts):
        """Updates the player"""
        # Change to new direction
        if self.nextDirection == "n":
            northProjection = BoundingBox(Point(self.boundingBox.pos.getX(), self.boundingBox.pos.getY() - 1), self.boundingBox.size)
            nCollision, box1 = world.isCollided(northProjection)

            if nCollision == False:
                self.direction = "n"
        elif self.nextDirection == "s":
            southProjection = BoundingBox(Point(self.boundingBox.pos.getX(), self.boundingBox.pos.getY() + 1), self.boundingBox.size)
            sCollision, box2 = world.isCollided(southProjection)

            if sCollision == False:
                self.direction = "s"
        elif self.nextDirection == "e":
            eastProjection = BoundingBox(Point(self.boundingBox.pos.getX() + 1, self.boundingBox.pos.getY()), self.boundingBox.size)
            eCollision, box3 = world.isCollided(eastProjection)

            if eCollision == False:
                self.direction = "e"
        elif self.nextDirection == "w":
            westProjection = BoundingBox(Point(self.boundingBox.pos.getX() - 1, self.boundingBox.pos.getY()), self.boundingBox.size)
            wCollision, box4 = world.isCollided(westProjection)

            if wCollision == False:
                self.direction = "w"

        # Velocity projection
        projected = [0, 0]
        if self.direction == 'n':
            # Calculate velocities
            projected[0] = 0
            projected[1] = -self.movmentSpeed
        if self.direction == 's':
            # Calculate velocities
            projected[0] = 0
            projected[1] = self.movmentSpeed
        if self.direction == 'e':
            # Calculate velocities
            projected[0] = self.movmentSpeed
            projected[1] = 0
        if self.direction == 'w':
            # Calculate velocities
            projected[0] = -self.movmentSpeed
            projected[1] = 0

        # Get normalized movement
        X = 0
        Y = 0
        if projected[0] > 0:
            X = -0.1
        elif projected[0] < 0:
            X = 0.1

        if projected[1] > 0:
            Y = -0.1
        elif projected[1] < 0:
            Y = 0.1

        # Get projected boundingbox
        self.projectedBox.pos = Point(self.boundingBox.pos.getX() - X, self.boundingBox.pos.getY() - Y)

        # Check collision based on projected position
        collision, box = world.isCollided(self.projectedBox)
        self.collided = collision # Used to stop advancing frames

        if collision:
            # Get intersection
            xIntersect = min(box.pos.getX() + box.size.getX(), self.boundingBox.pos.getX() + self.boundingBox.size.getX()) - max(box.pos.getX(), self.boundingBox.pos.getX())
            yIntersect = min(box.pos.getY() + box.size.getY(), self.boundingBox.pos.getY() + self.boundingBox.size.getY()) - max(box.pos.getY(), self.boundingBox.pos.getY())

            # Zero out velocity
            if not X == 0:
                projected[0] = xIntersect * (X * 10)

            if not Y == 0:
                projected[1] = yIntersect * (Y * 10)

        # Teleport if needed
        onTp = world.onTeleporter(self.projectedBox)
        if onTp != False:
            projected[0] = onTp.getX() - self.boundingBox.pos.getX()
            projected[1] = onTp.getY() - self.boundingBox.pos.getY()

        # Handle points
        for i in self.foodlist:
            if i.eaten(self.boundingBox.pos.getX(), self.boundingBox.pos.getY()):
                if i.powerpellet == True:
                    # Scare all the ghosts, its a power pellet
                    for g in ghosts:
                        g.scare()
                        self.lastScared = time.time()

                self.derenderingFood.append(i)

                # Remove food
                self.foodlist.remove(i)

                # Add points
                if i.powerpellet == True:
                    self.score += 50
                else:
                    self.score += 10

        # Death from ghost touch or win from no points left
        for g in ghosts:
            if BoundingBox.pointWithin(self.boundingBox, g.boundingBox):
                # If they arent scared, pacman is dead
                if g.scared == False:
                    # Count down
                    self.life -= 1

                    # Play death sound if sound has been enabled
                    if soundEnabled:
                        winsound.PlaySound("sounds/death.wav", winsound.SND_FILENAME)

                    # Close game if less than 3 lifes
                    if self.life < 1:
                        time.sleep(1)
                        self.respawn()
                        for g in ghosts: g.respawn(world, True)

                        self.alive = True
                        break
                    else:
                        self.alive = True
                        time.sleep(1)
                        self.respawn()

                        # Respawn all the ghosts
                        for g in ghosts:
                            g.respawn(world, True)

                        return 2
                else: # They are scared so theyre worth points
                    if g.alive == True:
                        self.score += 200 * self.ghostCount
                        self.ghostCount += 1
                        g.respawn(world)

        if len(self.foodlist) == 0:
            print("Win")
            self.alive = True
            self.winCallback()
            return True

        if self.alive == True:
            return True

        # Reset ghosts when scared timer is up
        if time.time() > self.lastScared + 7:
            for g in ghosts:
                self.ghostCount = 1
                g.scared = False

        # Move the box to the projected
        self.boundingBox.move(projected[0], projected[1])

        # Return false, (alive)
        return False

    def render(self, window):
        """Draws everything where its needed"""
        # Undraw images
        for p in self.images:
            p.undraw()

        # Redraw
        if self.direction == 'n':
            # Draw image
            if self.frame == 0:
                self.images[0].draw(window)
            else:
                self.images[1].draw(window)
        elif self.direction == 's':
            # Draw image
            if self.frame == 0:
                self.images[0].draw(window)
            else:
                self.images[2].draw(window)
        elif self.direction == 'e':
            # Draw image
            if self.frame == 0:
                self.images[0].draw(window)
            else:
                self.images[3].draw(window)
        elif self.direction == 'w':
            # Draw image
            if self.frame == 0:
                self.images[0].draw(window)
            else:
                self.images[4].draw(window)

        # Undraw all the food requested
        for food in self.derenderingFood:
            food.undrawFood()
            self.derenderingFood.remove(food)

        # Undraw based on life count
        if self.life != 3:
            self.lifeImages[self.life].undraw()

        # Update animation only if the player hasnt collided with anything
        if self.lastFrameTime + self.animationDelay < time.time() and self.collided == False:
            self.frame = not self.frame
            self.lastFrameTime = time.time()

        # Move the position to the bounding box
        toX = (self.boundingBox.pos.getX() - self.box.getP1().getX())
        toY = (self.boundingBox.pos.getY() - self.box.getP1().getY())

        self.box.move(toX, toY)
        for p in self.images:
            p.move(toX, toY)
