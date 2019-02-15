# TP3
# Patrick Kollman
# 112 Kinect Ping Pong

import pygame
import random
import math
import os
from pykinect2 import PyKinectV2
from pykinect2.PyKinectV2 import *
from pykinect2 import PyKinectRuntime
import ctypes
import _ctypes
import sys
if sys.hexversion >= 0x03000000:
    import _thread as thread
else:
    import thread

# initial framework
# CITATION: I recieved this Pygame framework online from class at blog.lukasperaza.com/getting-started-with-pygame/

class PygameGame(object):
    def mousePressed(self, x, y):
        pass

    def mouseReleased(self, x, y):
        pass

    def mouseMotion(self, x, y):
        pass

    def mouseDrag(self, x, y):
        pass

    def keyPressed(self, keyCode, modifier):
        pass

    def keyReleased(self, keyCode, modifier):
        pass

    def timerFired(self, dt):
        pass

    def redrawAll(self, screen):
        pass

    def isKeyPressed(self, key):
        ''' return whether a specific key is being held '''
        return self._keys.get(key, False)

    def __init__(self, width=1540, height=800, fps=50, title="112 Pygame Game"):
        self.width = width
        self.height = height
        self.fps = fps
        self.title = title
        self.bgColor = (255, 255, 255)
        pygame.init()
        self._infoObject = pygame.display.Info()

    def run(self):
        clock = pygame.time.Clock()
        screen = pygame.display.set_mode((self._infoObject.current_w >> 1, self._infoObject.current_h >> 1),pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE, 32)
        pygame.display.set_caption(self.title)

        # stores all the keys currently being held down
        self._keys = dict()

        # call game-specific initialization
        self.init()
        playing = True
        while playing:
            time = clock.tick(self.fps)
            self.timerFired(time)
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.mousePressed(*(event.pos))
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.mouseReleased(*(event.pos))
                elif (event.type == pygame.MOUSEMOTION and
                      event.buttons == (0, 0, 0)):
                    self.mouseMotion(*(event.pos))
                elif (event.type == pygame.MOUSEMOTION and
                      event.buttons[0] == 1):
                    self.mouseDrag(*(event.pos))
                elif event.type == pygame.KEYDOWN:
                    self._keys[event.key] = True
                    self.keyPressed(event.key, event.mod)
                elif event.type == pygame.KEYUP:
                    self._keys[event.key] = False
                    self.keyReleased(event.key, event.mod)
                elif event.type == pygame.QUIT:
                    playing = False
            screen.fill(self.bgColor)
            self.redrawAll(screen)
            pygame.display.flip()

        pygame.quit()

# Game class

class Game(PygameGame):
    def init(self):

        #KINECT 

        self._kinect = PyKinectRuntime.PyKinectRuntime(PyKinectV2.FrameSourceTypes_Color | PyKinectV2.FrameSourceTypes_Body)
        self._bodies = None
        self.rightHand = [-100,-100]
        self.isHandClosed = False

        ###### General

        self.gameMode = "splashScreen"
        self.playerScore = 0
        self.comScore = 0
        self.isPlaying = False
        self.playerServing = "Player1"
        self.gameOver = False
        self.winner = ""

        # net and table dimensions

        self.heightMargin = 250
        self.widthMargin = 400
        self.alter = 100
        self.topLeft = self.widthMargin+self.alter, self.heightMargin
        self.topRight = self.width-self.widthMargin-self.alter, self.heightMargin
        self.bottomLeft = self.widthMargin-self.alter, self.height-self.heightMargin
        self.bottomRight = self.width-self.widthMargin+self.alter, self.height-self.heightMargin
        self.centerY = (self.bottomLeft[1]+self.topLeft[1])//2
        self.leftCenterX = self.widthMargin
        self.rightCenterX = self.width-self.widthMargin
        self.widthSpacing = (self.rightCenterX-self.leftCenterX)//20
        self.netTop = self.centerY-40
        self.netBottom = self.centerY
        self.heightSpacing = (self.netTop-self.netBottom)//4
        
        # initialize kinect pic 

        folder = os.path.dirname(os.path.realpath(__file__))
        self.kinectPic = pygame.image.load(os.path.join(folder, "kinectPicture.png"))
         
        # initialize ball

        self.ballImage = pygame.transform.scale(pygame.image.load(os.path.join(folder, 'ping_pong_ball.png')).convert_alpha(), (20,20))
        self.ballSize = (pygame.Surface.get_size(self.ballImage))
        self.ballVelocity =[0,5]
        self.ballLocation = [self.width//2,self.bottomLeft[1]-60]
        self.ballDestination = [self.width//2,self.height//2]
        self.ballHeight = 10
        self.ballRadius = 20
        self.ballFalling = False
        self.ballCX = -100
        self.ballCY = -100
        
        # initialize paddle1

        self.paddle1Image = pygame.transform.scale(pygame.image.load(os.path.join(folder, 'ping_pong_paddle.png')).convert_alpha(), (70,70))
        self.paddle1Location = self.rightHand
        self.paddle1CanHit = True
        self.paddle1Size = (pygame.Surface.get_size(self.paddle1Image))
        self.rotatedPaddle1 = self.paddle1Image
        self.paddle1Width = self.paddle1Size[0]
        self.paddle1Height = self.paddle1Size[1]
        self.paddle1CX = self.paddle1Location[0]+self.paddle1Width//2
        self.paddle1CY = self.paddle1Location[1]+self.paddle1Height//2
        self.paddle1Degrees = 0
        self.prevRightHandHeight = 0
        self.curRightHandHeight = 0
        self.multiplier = 1
        
        # initialize paddle2

        self.paddle2Image = pygame.transform.scale(pygame.image.load(os.path.join(folder, 'ping_pong_paddle.png')).convert_alpha(), (70,70))
        self.paddle2Location = [self.width//2, self.topLeft[1]-80]
        self.paddle2CanHit = False
        self.paddle2Size = (pygame.Surface.get_size(self.paddle2Image))
        self.paddle2Width = self.paddle2Size[0]
        self.paddle2Height = self.paddle2Size[1]
        self.paddle2CX = self.paddle2Location[0]+self.paddle2Width//2
        self.paddle2CY = self.paddle2Location[1]+self.paddle2Height//2
        
    # create game modes

    def mousePressed(self, x, y):
        if (self.gameMode == "splashScreen"): 
            Game.splashScreenMousePressed(self, x, y)
        elif (self.gameMode == "playGame"):   
            Game.playGameMousePressed(self, x, y)
        elif (self.gameMode == "gameOver"):       
            Game.gameOverMousePressed(self, x, y)
    
    def keyPressed(self, code, mod):
        if (self.gameMode == "splashScreen"): 
            Game.splashScreenKeyPressed(self, code, mod)
        elif (self.gameMode == "playGame"):
            Game.playGameKeyPressed(self, code, mod)
        elif (self.gameMode == "gameOver"):       
            Game.gameOverKeyPressed(self, code, mod)
    
    def timerFired(self, dt):
        if (self.gameMode == "splashScreen"): 
            Game.splashScreenTimerFired(self, dt)
        elif (self.gameMode == "playGame"):
            Game.playGameTimerFired(self, dt)
        elif (self.gameMode == "gameOver"):
            Game.gameOverTimerFired(self, dt)
            
    
    def redrawAll(self, screen):
        if (self.gameMode == "splashScreen"): 
            Game.splashScreenRedrawAll(self, screen)
        elif (self.gameMode == "playGame"):   
            Game.playGameRedrawAll(self, screen)
        elif (self.gameMode == "gameOver"):       
            Game.gameOverRedrawAll(self, screen)
    
    # splash screen Functions
    
    @staticmethod
    def splashScreenMousePressed(self, x, y):
        self.gameMode = "playGame"
        ###### General
        self.playerScore = 0
        self.comScore = 0
        self.isPlaying = False
        self.playerServing = "Player1"
        self.gameOver = False
        # initialize ball
        self.lastThingHit = ""
        self.ballVelocity =[0,5]
        self.ballLocation = [self.width//2,self.bottomLeft[1]-60]
        self.ballDestination = [self.width//2,self.height//2]
        self.ballHeight = 10
        self.ballRadius = 20
        self.ballFalling = False
        self.ballCX = -100
        self.ballCY = -100
        # initialize paddle1
        self.paddle1Location = self.rightHand
        self.paddle1CanHit = True
        self.paddle1Size = (pygame.Surface.get_size(self.paddle1Image))
        self.rotatedPaddle1 = self.paddle1Image
        self.paddle1Width = self.paddle1Size[0]
        self.paddle1Height = self.paddle1Size[1]
        self.paddle1CX = self.paddle1Location[0]+self.paddle1Width//2
        self.paddle1CY = self.paddle1Location[1]+self.paddle1Height//2
        self.paddle1Degrees = 0
        # initialize paddle2
        self.paddle2Location = [self.width//2, self.topLeft[1]-80]
        self.paddle2CanHit = False
        self.paddle2Size = (pygame.Surface.get_size(self.paddle2Image))
        self.paddle2Width = self.paddle2Size[0]
        self.paddle2Height = self.paddle2Size[1]
        self.paddle2CX = self.paddle2Location[0]+self.paddle2Width//2
        self.paddle2CY = self.paddle2Location[1]+self.paddle2Height//2
    
    @staticmethod
    def splashScreenKeyPressed(self, code, mod):
        pass
    
    @staticmethod    
    def splashScreenTimerFired(self,dt):
        # CITATION: I partially recieved this code from https://github.com/Kinect/PyKinect2/blob/master/examples/PyKinectBodyGame.py
        if self._kinect.has_new_body_frame(): 
            self._bodies = self._kinect.get_last_body_frame()
            # --- draw skeletons to _frame_surface
        if self._bodies is not None: 
            for i in range(0, self._kinect.max_body_count):
                body = self._bodies.bodies[i]
                if not body.is_tracked: 
                    continue 
                joints = body.joints
        ####### END OF CITATION
                # convert joint coordinates to color space 

                joint_points = self._kinect.body_joints_to_color_space(joints)

                jointPoints = joint_points
                hand = PyKinectV2.JointType_HandRight
                left = PyKinectV2.JointType_HandLeft

                handState = joints[hand].TrackingState
                leftState = joints[left].TrackingState

                # both joints are not tracked
                if (handState == PyKinectV2.TrackingState_NotTracked) and (leftState == PyKinectV2.TrackingState_NotTracked): 
                    return

                # both joints are not *really* tracked
                if (handState == PyKinectV2.TrackingState_Inferred) and (leftState == PyKinectV2.TrackingState_Inferred):
                    return

                ###### END OF CITATION

                handLocationx, handLocationy = (jointPoints[hand].x), (jointPoints[hand].y)
                leftLocationx, leftLocationy = (jointPoints[left].x), (jointPoints[left].y)
                d = math.sqrt((handLocationx-leftLocationx)**2 + (handLocationy-leftLocationy)**2)

                if d<5:
                    self.gameMode = "playGame"
                    ###### General
                    self.playerScore = 0
                    self.comScore = 0
                    self.isPlaying = False
                    self.playerServing = "Player1"
                    self.gameOver = False
                    # initialize ball
                    self.lastThingHit = ""
                    self.ballVelocity =[0,5]
                    self.ballLocation = [self.width//2,self.bottomLeft[1]-60]
                    self.ballDestination = [self.width//2,self.height//2]
                    self.ballHeight = 10
                    self.ballRadius = 20
                    self.ballFalling = False
                    self.ballCX = -100
                    self.ballCY = -100
                    # initialize paddle1
                    self.paddle1Location = self.rightHand
                    self.paddle1CanHit = True
                    self.paddle1Size = (pygame.Surface.get_size(self.paddle1Image))
                    self.rotatedPaddle1 = self.paddle1Image
                    self.paddle1Width = self.paddle1Size[0]
                    self.paddle1Height = self.paddle1Size[1]
                    self.paddle1CX = self.paddle1Location[0]+self.paddle1Width//2
                    self.paddle1CY = self.paddle1Location[1]+self.paddle1Height//2
                    self.paddle1Degrees = 0
                    # initialize paddle2
                    self.paddle2Location = [self.width//2, self.topLeft[1]-80]
                    self.paddle2CanHit = False
                    self.paddle2Size = (pygame.Surface.get_size(self.paddle2Image))
                    self.paddle2Width = self.paddle2Size[0]
                    self.paddle2Height = self.paddle2Size[1]
                    self.paddle2CX = self.paddle2Location[0]+self.paddle2Width//2
                    self.paddle2CY = self.paddle2Location[1]+self.paddle2Height//2
         
         
    @staticmethod    
    def splashScreenRedrawAll(self, screen):

        screen.fill((56,79,90))

        # draw text
        
        myFont = pygame.font.SysFont("monospace", 50)
        
        title = myFont.render("Kinect Ping Pong", True, (255,0,0))
        textBox = title.get_rect(center = (self.width//2,self.height//4))
        screen.blit(title, textBox)
        
        instructions = myFont.render("Clap to begin!", True, (255,0,0))
        instructBox = instructions.get_rect\
        (center=(self.width//2,self.height*3//4))
        screen.blit(instructions, instructBox)
        
        # draw kinect picture
        
        kinectRect = self.kinectPic.get_rect(center=(self.width//2,self.height//2))
        self.kinectPic = pygame.transform.scale(self.kinectPic,(600,200))
        screen.blit(self.kinectPic,kinectRect)
        
    # gameOver screen Functions
    
    @staticmethod
    def gameOverMousePressed(self, x ,y):
        pass
    
    @staticmethod
    def gameOverKeyPressed(self, code, mod):
        if code == pygame.K_r:
            self.gameMode = "splashScreen"
    
    @staticmethod    
    def gameOverTimerFired(self,dt):
        # CITATION: I partially recieved this code from https://github.com/Kinect/PyKinect2/blob/master/examples/PyKinectBodyGame.py
        if self._kinect.has_new_body_frame(): 
            self._bodies = self._kinect.get_last_body_frame()
            # --- draw skeletons to _frame_surface
        if self._bodies is not None: 
            for i in range(0, self._kinect.max_body_count):
                body = self._bodies.bodies[i]
                if not body.is_tracked: 
                    continue 
                joints = body.joints
        ####### END OF CITATION
                # convert joint coordinates to color space 

                joint_points = self._kinect.body_joints_to_color_space(joints)

                jointPoints = joint_points
                hand = PyKinectV2.JointType_HandRight
                left = PyKinectV2.JointType_HandLeft

                handState = joints[hand].TrackingState
                leftState = joints[left].TrackingState

                # both joints are not tracked
                if (handState == PyKinectV2.TrackingState_NotTracked) and (leftState == PyKinectV2.TrackingState_NotTracked): 
                    return

                # both joints are not *really* tracked
                if (handState == PyKinectV2.TrackingState_Inferred) and (leftState == PyKinectV2.TrackingState_Inferred):
                    return

                ###### END OF CITATION

                handLocationx, handLocationy = (jointPoints[hand].x), (jointPoints[hand].y)
                leftLocationx, leftLocationy = (jointPoints[left].x), (jointPoints[left].y)
                d = math.sqrt((handLocationx-leftLocationx)**2 + (handLocationy-leftLocationy)**2)

                if d<5:
                    self.gameMode = "splashScreen"

    
    @staticmethod    
    def gameOverRedrawAll(self, screen):

        # prepare screen and font

        screen.fill((0,255,0))
        if self.winner == "THE COMPUTER":
            screen.fill((255,0,0))
        myFont = pygame.font.SysFont("monospace", 50)
        
        # display winner 

        victor = "%s WON!" % self.winner
        winner = myFont.render(victor, True, (0,0,0))
        winnerBox = winner.get_rect(center= (self.width//2, self.height//4))
        screen.blit(winner, winnerBox)

        # display score
        
        loserScore = self.playerScore
        if self.playerScore == 11:
            loserScore = self.comScore
        score = "11 - %d" % loserScore
        words = myFont.render(score,True,(0,0,0))
        wordsBox = words.get_rect(center = (self.width//2, self.height//2))
        screen.blit(words, wordsBox)

        # display instructions
        
        text = "Clap to"
        text2 = "play again."
        instructions = myFont.render(text,True, (0,0,0))
        instructions2 = myFont.render(text2,True,(0,0,0))
        textBox = instructions.get_rect(center = (self.width//2, self.height*3//4))
        textBox2 = instructions2.get_rect(center=(self.width//2, self.height*4//5))
        screen.blit(instructions, textBox)
        screen.blit(instructions2, textBox2)
        
    # playGame Functions
    
    @staticmethod
    def playGameMousePressed(self, x ,y):
        pass
    
    @staticmethod    
    def playGameKeyPressed(self, code, mod):
        if code == pygame.K_r:
            self.gameMode = "splashScreen"
    
    ################### playGameTimerFired beginning    

    @staticmethod
    def playGameTimerFired(self, dt):

        #self.paddle1Location = pygame.mouse.get_pos()

        ########################### KINECT LOGIC

        # CITATION: I partially recieved this code from https://github.com/Kinect/PyKinect2/blob/master/examples/PyKinectBodyGame.py
        if self._kinect.has_new_body_frame(): 
            self._bodies = self._kinect.get_last_body_frame()
            # --- draw skeletons to _frame_surface
        if self._bodies is not None: 
            for i in range(0, self._kinect.max_body_count):
                body = self._bodies.bodies[i]
                if not body.is_tracked: 
                    continue 
                joints = body.joints
        ####### END OF CITATION
                # convert joint coordinates to color space 

                joint_points = self._kinect.body_joints_to_color_space(joints)
              
                Game.updatePaddle1(self,joints,joint_points)

                Game.rotatePaddle(self,joints,joint_points)


        ########################## GAME LOGIC
        
        # dimensions and coordinates
            # paddle 1
        paddle1x, paddle1y = self.paddle1Location[0],self.paddle1Location[1]
        paddle1Width, paddle1Height = self.paddle1Size[0],self.paddle1Size[1]
        paddle1CX, paddle1CY, = paddle1x+paddle1Width//2, paddle1y+paddle1Height//2
        self.paddle1CX, self.paddle1CY = paddle1CX, paddle1CY
        
            # paddle 2
        paddle2x, paddle2y = self.paddle2Location[0],self.paddle2Location[1]
        paddle2Width, paddle2Height = self.paddle2Size[0],self.paddle2Size[1]
        paddle2CX, paddle2CY, = paddle2x+paddle2Width//2, paddle2y+paddle2Height//2
        self.paddle2CX, self.paddle2CY = paddle2CX, paddle2CY
        
            # ball
        ballx, bally = self.ballLocation[0],self.ballLocation[1]
        ballWidth, ballHeight = self.ballSize[0], self.ballSize[1]
        ballCX, ballCY = ballx+ballWidth//2,bally+ballHeight//2
        self.ballCX, self.ballCY = ballCX, ballCY
        
        # if the computer is serving

        if self.playerServing == "Computer" and (not self.isPlaying):
            Game.moveAI(self)

        # begin the game if someone serves
        
        if (not self.isPlaying) and (Game.paddle1Hit(self) or Game.paddle2Hit(self)):
            self.ballHeight -= 25
            self.isPlaying = True
        
        if self.isPlaying: # the game has now begun

            # hitting ball mechanics
            
            if Game.paddle1Hit(self): # if the ball hit paddle1
                self.lastThingHit = "paddle1"
                Game.changeVelocity(self,1)
                self.ballVelocity[1] *= self.multiplier
                self.paddle1CanHit = False
                self.paddle2CanHit = True
                self.ballFalling = True
                self.ballDestination = Game.findDestination(self)
                if self.ballHeight<35:
                    self.ballHeight += 25
            
            if Game.paddle2Hit(self): # if the ball hit paddle2
                self.lastThingHit = "paddle2"
                Game.changeVelocity(self,2)
                self.ballVelocity[1] = 5
                self.paddle1CanHit = True
                self.paddle2CanHit = False
                self.ballFalling = True
                if self.ballHeight<35:
                    self.ballHeight += 25

            # Computer Movement
        
            Game.moveAI(self)

            Game.ballUpdate(self) # update ball and see if anyone scored
                
     
    ##################################################### playGameTimerFired over

    ##################################################### Functions for playGameTimerFired 

    @staticmethod
    def playerScored(self): 
        self.lastThingHit = ""
        self.playerServing = "Player1"
        self.paddle2Location = [self.width//2, self.topLeft[1]-80]
        self.playerScore+=1
        self.isPlaying = False
        self.paddle1CanHit = True
        self.paddle2CanHit = False
        self.ballFalling = False
        self.ballHeight = 10
        self.paddle1CanHit = True
        self.ballVelocity = [0,5]
        # place ball on player's side
        self.ballLocation = [self.width//2,self.bottomLeft[1]-60]
        if self.playerScore == 11:
            self.gameMode = "gameOver"
            self.winner = "YOU"

    @staticmethod
    def computerScored(self):
        self.lastThingHit = ""
        self.playerServing = "Computer"
        self.comScore+=1
        self.isPlaying = False
        self.ballFalling = False
        self.ballHeight = 10
        self.ballLocation = [self.width//2,self.height-150]
        self.paddle1CanHit = False
        self.paddle2CanHit = True
        self.ballVelocity = [0,-5]
        # place ball at computers side
        lst = [self.topLeft[0],self.topRight[0]]
        rad = lst[random.randint(0,1)]
        self.paddle2Location = [rad, self.topLeft[1]-80]
        self.ballLocation = [self.width//2, self.paddle2CY-5]
        ######################
        if self.comScore == 11:
            self.gameMode = "gameOver"
            self.winner = "THE COMPUTER"

    # CITATION: I recieved this function from http://www.ariel.com.au/a/python-point-int-poly.html
    @staticmethod 
    def pointInsidePolygon(x,y,poly): # checks to see if a point is inside a polygon
        n = len(poly)
        inside =False
        p1x,p1y = poly[0]
        for i in range(n+1):
            p2x,p2y = poly[i % n]
            if y > min(p1y,p2y):
                if y <= max(p1y,p2y):
                    if x <= max(p1x,p2x):
                        if p1y != p2y:
                            xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x,p1y = p2x,p2y
        return inside

    @staticmethod
    def updatePaddle1(self, joints, jointPoints): # update paddle1 based on the right hand

        joint = PyKinectV2.JointType_HandRight

        #CITATION: I partially recieved this code from https://github.com/Kinect/PyKinect2/blob/master/examples/PyKinectBodyGame.py

        jointState = joints[joint].TrackingState

        # both joints are not tracked
        if (jointState == PyKinectV2.TrackingState_NotTracked): 
            return

        # both joints are not *really* tracked
        if (jointState == PyKinectV2.TrackingState_Inferred):
            return

        ###### END OF CITATION

        location = (int(jointPoints[joint].x)-350, int(jointPoints[joint].y)-80)
        self.rightHand = location
        self.paddle1Location = self.rightHand

        # save the hand positions
        if joints[PyKinectV2.JointType_HandRight].TrackingState != PyKinectV2.TrackingState_NotTracked:
            self.curRightHandHeight = joints[PyKinectV2.JointType_HandRight].Position.y

        # calculate speed multiplier of hand speed
        self.multiplier = 1 + abs((self.prevRightHandHeight - self.curRightHandHeight)*20)
        if math.isnan(self.multiplier) or self.multiplier < 0:
            self.multiplier = 1

        # cycle previous and current heights for next time
        self.prevRightHandHeight = self.curRightHandHeight

    @staticmethod
    def rotatePaddle(self, joints, joint_points): # rotate the paddle so it is held naturally
        jointPoints = joint_points
        hand = PyKinectV2.JointType_HandRight
        thumb = PyKinectV2.JointType_ThumbRight

        handState = joints[hand].TrackingState
        thumbState = joints[thumb].TrackingState

        # both joints are not tracked
        if (handState == PyKinectV2.TrackingState_NotTracked) and (thumbState == PyKinectV2.TrackingState_NotTracked): 
            return

        # both joints are not *really* tracked
        if (handState == PyKinectV2.TrackingState_Inferred) and (thumbState == PyKinectV2.TrackingState_Inferred):
            return

        ###### END OF CITATION

        handLocation = [int(jointPoints[hand].x), int(jointPoints[hand].y)]
        thumbLocation = [int(jointPoints[thumb].x), int(jointPoints[thumb].y)]

        dy = -(thumbLocation[1]-handLocation[1])  
        dx = (thumbLocation[0]-handLocation[0])
        angle = math.degrees(math.atan2(dy, dx)) - 180
        
        # rotate paddle
        self.rotatedPaddle1 = pygame.transform.rotate(self.paddle1Image,angle)

    @staticmethod
    def paddle1Hit(self): # if the ball hits paddle1
        r = 30
        d = math.sqrt((self.ballCX-self.paddle1CX)**2 + (self.ballCY-self.paddle1CY)**2)
        if d < r and self.paddle1CanHit:
            return True
        
    @staticmethod
    def paddle2Hit(self): # if the ball hits paddle2
        r = 30
        d = math.sqrt((self.ballCX-self.paddle2CX)**2 + (self.ballCY-self.paddle2CY)**2)
        if d < r and self.paddle2CanHit:
            return True

    @staticmethod
    def ballUpdate(self): # change the ball's location and check to see if someone scored
        # update location

        self.ballLocation[0] += self.ballVelocity[0]
        self.ballLocation[1] += self.ballVelocity[1]
       
        if self.ballFalling == True:
            self.ballHeight -= 0.7
            if self.ballHeight <= 0:
                self.ballFalling = False

        elif self.ballFalling == False:
            self.ballHeight += 0.7
            if self.ballHeight >= 10:
                self.ballFalling = True

        x = self.ballCX
        y = self.ballCY
        polyTop = [[self.leftCenterX,self.centerY],self.topLeft,self.topRight,[self.rightCenterX,self.centerY]]
        polyBottom = [self.bottomLeft,[self.leftCenterX,self.centerY],[self.rightCenterX,self.centerY],self.bottomRight]

        # check to see if someone scored

        # check if bounced twice on computers side (player scored)
        if Game.pointInsidePolygon(x,y,polyTop) and self.ballHeight<=0:
            thingHit = "top"
            if self.lastThingHit == thingHit:
                Game.playerScored(self)
            self.lastThingHit = "top"
        # check if bounced twice on players side (computer scored)
        elif Game.pointInsidePolygon(x,y,polyBottom) and self.ballHeight<=0:
            thingHit = "bottom"
            if self.lastThingHit == thingHit:
                Game.computerScored(self)
            self.lastThingHit = thingHit
        # if the ball bounces off the table see who scores
        elif not(Game.pointInsidePolygon(x,y,polyBottom) or Game.pointInsidePolygon(x,y,polyTop)) and self.ballHeight<=0:
            last = self.lastThingHit
            if last == "top" or last == "paddle2":
                Game.playerScored(self)
            elif last == "bottom" or last == "paddle1":
                Game.computerScored(self)


    @staticmethod 
    def moveAI(self): 
        vx = self.ballVelocity[0]
        bx = self.ballDestination[0]
        speed = 4 # you can increase difficulty by increasing speed

        # if the computer is serving and game has not begun... serve
        if not self.isPlaying:
            if self.paddle2CX > self.ballCX:
                self.paddle2Location[0] -= speed
            elif self.paddle2CX < self.ballCX:
                self.paddle2Location[0] += speed

        # if the game has begun react to the ball's destination
        # the computer has the capability of missing since the speed and inequalities don't always divide evenly
        if self.isPlaying:
            if abs(bx - self.paddle2CX) > 3:
                if self.paddle2CX > bx:
                    self.paddle2Location[0] -= speed
            
                if self.paddle2CX < bx:
                    self.paddle2Location[0] += speed

    @staticmethod
    def findDestination(self): # calculate the ball's destination after it hits paddle1
        vx, vy= self.ballVelocity[0], self.ballVelocity[1]
        yFinal = self.paddle2CY
        dy = (yFinal - self.ballCY)
        t = 0
        if vy!=0:
            t = dy/vy
        xFinal = (t*vx) + self.ballCX
        destination = [xFinal,yFinal]
        return destination

    @staticmethod
    def changeVelocity(self, paddleNumber): # velocity mechanics
        self.ballVelocity[1] = -1*self.ballVelocity[1]
        if paddleNumber ==1:
            if self.paddle1CX < self.ballCX:
                self.ballVelocity[0] = (self.ballCX - self.paddle1CX)//6
            elif self.paddle1CX > self.ballCX:
                self.ballVelocity[0] = (self.ballCX - self.paddle1CX)//6
        else:
            if self.paddle2CX < self.ballCX:
                self.ballVelocity[0] = (self.ballCX - self.paddle2CX)//6
            elif self.paddle2CX > self.ballCX:
                self.ballVelocity[0] = (self.ballCX - self.paddle2CX)//6
            
    ######################################## DRAWING

    @staticmethod
    def playGameRedrawAll(self, screen):
        # draw Table
        Game.drawTable(self,screen)
        # draw paddle2
        screen.blit(self.paddle2Image, (self.paddle2Location))
        # draw ball shadow
        Game.drawShadow(self,screen)
        # draw ball
        screen.blit(self.ballImage,(self.ballLocation)) 
        # draw paddle1
        screen.blit(self.rotatedPaddle1,(self.paddle1Location))
        # draw scores
        myFont = pygame.font.SysFont("monospace", 50)
        userScore = "Player 1 Score: %d" % self.playerScore
        comScore = "Computer Score: %d" % self.comScore
        playerScore = myFont.render(userScore, True, (255,0,0))
        computerScore = myFont.render(comScore, True, (0,255,0))
        textBox = playerScore.get_rect(center = (self.width//2,self.height-50))
        comBox = computerScore.get_rect(center=(self.width//2,50))
        screen.blit(playerScore, textBox)
        screen.blit(computerScore, comBox)
     
    @staticmethod
    def drawShadow(self,screen): # provides a "height" to the ball

        cx, cy = self.ballLocation[0], self.ballLocation[1]+self.ballRadius*3//4
        cy = cy+5*self.ballHeight

        pygame.draw.ellipse(screen,(125,125,125),(cx,cy,20,10))

    @staticmethod
    def drawTable(self,screen):

        heightMargin = self.heightMargin
        widthMargin = self.widthMargin
        width = self.width
        height = self.height
        alter = self.alter

        # draw background
        screen.fill((125,125,125))

        # draw table and borders

        topLeft = self.topLeft
        topRight = self.topRight
        bottomLeft = self.bottomLeft
        bottomRight = self.bottomRight

        pygame.draw.polygon(screen,(0,191,255),(topLeft,topRight,bottomRight,bottomLeft))
        pygame.draw.line(screen,(255,255,255),(width//2,heightMargin),(width//2,height-heightMargin), 5)
        pygame.draw.polygon(screen,(255,255,255),(topLeft,topRight,bottomRight,bottomLeft), 5)

        # draw legs

        pygame.draw.line(screen,(50,50,50),bottomLeft,(bottomLeft[0],height-heightMargin//3),20)
        pygame.draw.line(screen,(50,50,50),bottomRight,(bottomRight[0],height-heightMargin//3),20)

        # draw net

        centerY = (bottomLeft[1]+topLeft[1])//2
        leftCenterX = widthMargin
        rightCenterX = width-widthMargin
        widthSpacing = (rightCenterX-leftCenterX)//20
        netTop = centerY-40
        netBottom = centerY
        heightSpacing = (netTop-netBottom)//4

        centerY = self.centerY
        leftCenterX = self.leftCenterX
        rightCenterX = self.rightCenterX
        widthSpacing = self.widthSpacing
        netTop = self.netTop
        netBottom = self.netBottom
        heightSpacing = self.heightSpacing

        for i in range(21):
            pygame.draw.line(screen,(0,0,0),(leftCenterX+i*widthSpacing,netTop),(leftCenterX+i*widthSpacing,netBottom),3)
        for j in range(5):
            pygame.draw.line(screen,(0,0,0),(widthMargin,netBottom+j*heightSpacing),(width-widthMargin,netBottom+j*heightSpacing),3)
        pygame.draw.line(screen,(255,0,0),(widthMargin,netTop),(width-widthMargin,netTop),10)
        


Game().run()