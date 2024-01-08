import pygame as pg
from pygame import mixer
import os
import random
import csv
import button

mixer.init()
pg.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pg.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pg.display.set_caption('Metal Soldier')

#フレームレート設定
clock = pg.time.Clock()
FPS = 60

#下向きに加わる力
GRAVITY = 0.75
SCROLL_THRESH = 200
ROWS = 16 #ステージの行(縦の大きさ)
COLS = 150 #ステージの列(長さ)
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 25
screen_scroll = 0
bg_scroll = 0
level = 1
MAX_LEVELS = 3
start_game = False
start_intro = False

#プレイヤーの動き
moving_left = False
moving_right = False
shoot = False
bomb = False
bomb_thrown = False

#音楽のロード
jump_fx = pg.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.5)
shot_fx = pg.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0.5)
bomb_fx = pg.mixer.Sound('audio/bomb.wav')
bomb_fx.set_volume(0.5)


#画像のロード
#ボタンの画像
start_img = pg.image.load('img/start_btn.png').convert_alpha()
exit_img = pg.image.load('img/exit_btn.png').convert_alpha()
restart_img = pg.image.load('img/restart_btn.png').convert_alpha()

#背景画像
pine1_img = pg.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pg.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pg.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pg.image.load('img/Background/sky.png').convert_alpha()
sky2_img = pg.image.load('img/Background/sky2.png').convert_alpha()
title_img = pg.image.load('img/Background/title.png') 
#画像のリスト
img_list = []
for x in range(TILE_TYPES):
    img = pg.image.load(f'img/Tile/{x}.png')
    img = pg.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)
#弾
bullet_img = pg.image.load('img/icons/bullet.png').convert_alpha()
#爆弾
bomb_img = pg.image.load('img/icons/bomb.png').convert_alpha()
#アイテム
repair_box_img = pg.image.load('img/icons/repair_box.png').convert_alpha()
ammo_box_img = pg.image.load('img/icons/ammo_box.png').convert_alpha()
bomb_box_img = pg.image.load('img/icons/bomb_box.png').convert_alpha()
item_boxes = {'Repair' : repair_box_img,
              'Ammo' : ammo_box_img,
              'Bomb' : bomb_box_img
              }


#色の定義
BG = (144,201,120)
RED = (255,0,0)
GREEN = (0,255,0)
PINK = (235, 65, 54)
WHITE = (255,255,255)
BLACK = (0,0,0)


#フォントの定義
font = pg.font.SysFont('Futura', 30)

#テキストの表示
def draw_text(text, font, text_col, x, y):
    img = font.render(text,True,text_col)
    screen.blit(img, (x,y))

#背景
def draw_bg():
    screen.fill(BG)
    width = sky_img.get_width()
    for x in range(5):
        if level == 1:
            screen.blit(sky2_img, ((x * width) - bg_scroll * 0.5, 0))
            screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
        else:
            screen.blit(sky_img, ((x * width) - bg_scroll * 0.5, 0))
        screen.blit(pine1_img, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
        screen.blit(pine2_img, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))

#レベルリセット
def restert_level():
    enemy_group.empty()
    bullet_group.empty()            
    bomb_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()    

    #空のリスト
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)

    return data    

#プレイヤー、敵1,2
class Soldier(pg.sprite.Sprite):
    def __init__(self,char_type,x,y,scale,speed,ammo,bombs):
        pg.sprite.Sprite.__init__(self)
        self.alive = True #生きているかどうか
        self.char_type = char_type #プレイヤーまたは敵
        self.speed = speed #移動速度
        self.ammo = ammo #弾数
        self.start_ammo = ammo
        self.bombs = bombs #弾数(爆弾)
        self.shoot_cooldown = 0 #射撃の間隔
        self.health = 100 #体力
        self.max_health = self.health
        self.direction = 1 #キャラクターの向き
        self.vel_y = 0 #上下に加わる力
        self.jump = False  #ジャンプ
        self.in_air = True #空中にいるかどうか
        self.flip = False #方向転換
        self.animation_list = [] #アニメーションを格納
        self.frame_index = 0 #アニメーションの再生
        self.action = 0 #アクション
        self.update_time = pg.time.get_ticks() #ゲーム内時間
        #aiの動き
        self.move_counter = 0
        self.vision = pg.Rect(0,0,150,20)
        self.idling = False
        self.idling_counter = 0
        self.bomb_cooldown = 0

        #プレイヤー画像
        animation_types = ['Idle','Run','Jump','Death'] #アクションの種類
        for animation in animation_types:
          temp_list = []
          #フォルダー内のファイルの数をカウント
          num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
          #モーション###
          for i in range(num_of_frames):
              img = pg.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
              img = pg.transform.scale(img, (int(img.get_width()*scale), int(img.get_height()*scale)))
              temp_list.append(img)
          self.animation_list.append(temp_list)    
          ################                
        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.width = self.image.get_width() 
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        #クールダウン更新
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.bomb_cooldown > 0:
            self.bomb_cooldown -= 1 

    def move(self, moving_left, moving_right):
        screen_scroll = 0
        dx = 0
        dy = 0
        
        #左右移動
        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1
        #ジャンプ    
        if self.jump == True and self.in_air == False:
            self.vel_y = -14
            self.jump = False
            self.in_air = True

        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y
        dy += self.vel_y


        #接触の確認
        for tile in world.obstacle_list:
            #x方向の衝突確認
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                #aiが衝突
                if self.char_type == 'enemy':
                    self.direction *= -1
                    self.move_counter = 0
            #y方向の衝突確認
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom                    


        #水に触れたとき
        if pg.sprite.spritecollide(self, water_group, False):
            self.health = 0

        #看板に触れたとき
        level_complete = False    
        if pg.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        #ステージ下に    
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0    

        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0

        self.rect.x += dx    
        self.rect.y += dy

        #プレイヤーの位置によって画面を移動
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH)\
                  or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll, level_complete    

    def shoot(self):
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            #self.rect.size[0]に掛ける数によって発射位置を調整。数字が大きいほど前から発射。
            bullet = Bullet(self.rect.centerx + (0.7 * self.rect.size[0] * self.direction),self.rect.centery,self.direction)
            bullet_group.add(bullet)
            #弾を減らす
            self.ammo -= 1
            shot_fx.play()

    def enemy_bomb(self):
        if self.bomb_cooldown == 0:
            self.bomb_cooldown = 50            
            bomb = Bomb(enemy.rect.centerx + (0.5 * enemy.rect.size[0] * enemy.direction),\
                enemy.rect.top,enemy.direction)
            bomb_group.add(bomb)                       

    #ランダムに動くai
    def ai(self):
        if self.alive and player.alive:
            if self.idling == False and random.randint(1, 200) == 1:
                self.update_action(0)#0：待機
                self.idling = True
                self.idling_counter = 50
            #近くにプレイヤーがいるか確認    
            if self.vision.colliderect(player.rect):
                    #移動を止め、プレイヤーの方向を向く
                    self.update_action(0)#0：待機
                    #プレイヤーに撃つ
                    if self.char_type == 'enemy':
                        self.shoot()
                    #爆弾    
                    elif self.char_type == 'enemy2':
                        self.enemy_bomb()

            else:        
                if self.idling == False:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False 
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right) 
                    self.update_action(1)#1：移動
                    self.move_counter += 1
                    #敵の動きai
                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                    #索敵範囲の視覚化
                    #pg.draw.rect(screen, RED, self.vision)


                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1     
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False         
        #スクロール
        self.rect.x += screen_scroll

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        self.image = self.animation_list[self.action][self.frame_index]
        if pg.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pg.time.get_ticks()
            self.frame_index += 1
         #アニメーションが終了した場合初めから   
        if self.frame_index >= len(self.animation_list[self.action]):
                if self.action == 3:
                    self.frame_index = len(self.animation_list[self.action]) - 1
                else:
                    self.frame_index = 0

    def update_action(self,new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pg.time.get_ticks()



    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False  
            self.update_action(3)
        
    def draw(self):    
        screen.blit(pg.transform.flip(self.image,self.flip,False),self.rect)


class World():
    def __init__(self):
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE 
                    tile_data = (img, img_rect)
                    if tile >= 0 and tile <= 11:
                        self.obstacle_list.append(tile_data)
                    elif tile >= 12 and tile <= 13: #水
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water) 
                    elif tile >= 14 and tile <= 17: #装飾
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration) 
                    elif tile == 18: #プレイヤー  
                        player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1, 6, 20, 4)#移動速度やスケールの数値
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 19: #敵
                        enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1, 3, 100000, 0)#移動速度やスケールの数値
                        enemy_group.add(enemy) 
                    elif tile == 20: #弾薬   
                        item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 21: #爆弾    
                        item_box = ItemBox('Bomb', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 22: #修理
                        item_box = ItemBox('Repair', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 23: #出口
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)
                    elif tile == 24: #敵2
                        enemy2 = Soldier('enemy2', x * TILE_SIZE, y * TILE_SIZE, 1, 5, 100000, 0)#移動速度やスケールの数値
                        enemy_group.add(enemy2)                        

        return player, health_bar                


    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])


class Decoration(pg.sprite.Sprite):
    def __init__(self,img,x,y):
        pg.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class Water(pg.sprite.Sprite):
    def __init__(self,img,x,y):
        pg.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class Exit(pg.sprite.Sprite):
    def __init__(self,img,x,y):
        pg.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll

class ItemBox(pg.sprite.Sprite):
    def __init__(self,item_type,x,y):
        pg.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        #スクロール
        self.rect.x += screen_scroll        
        #アイテムとプレイヤーの接触確認
        if pg.sprite.collide_rect(self,player):
            #アイテムの種類確認
            if self.item_type == 'Repair':
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Ammo':
                player.ammo += 15   
            elif self.item_type == 'Bomb':
                player.bombs += 3
            #アイテムの表示消す
            self.kill()        


class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        #体力の更新
        self.health = health
        #体力の現在値と最大値の比率
        ratio = self.health / self.max_health
        pg.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))        
        pg.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pg.draw.rect(screen, GREEN, (self.x, self.y, 150*ratio, 20))        


class Bullet(pg.sprite.Sprite):
    def __init__(self,x,y,direction):
        pg.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.direction = direction
        

    def update(self):
        #弾の動き
        self.rect.x += (self.direction * self.speed) + screen_scroll
        #弾が画面から消えたか確認
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()
        #壁に衝突
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()
        #弾の衝突時
        if pg.sprite.spritecollide(player,bullet_group,False):
            if player.alive:
                player.health -= 5
                self.kill()
        for enemy in enemy_group:
            if pg.sprite.spritecollide(enemy,bullet_group,False):
                if enemy.alive:
                    enemy.health -= 35
                    self.kill()                



class Bomb(pg.sprite.Sprite):
    def __init__(self,x,y,direction):
        pg.sprite.Sprite.__init__(self)
        self.timer = 80
        self.vel_y = -11
        self.speed = 7
        self.image = bomb_img
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.width = self.image.get_width()
        self.height = self.image.get_height()        
        self.direction = direction

    def update(self):
        self.vel_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.vel_y
        #壁の衝突
        for tile in world.obstacle_list:
        #壁に衝突した場合
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed            
                        #y方向の衝突確認
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom  

        #爆弾位置
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        #カウントダウン
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            bomb_fx.play()       
            explosion = Explosion(self.rect.x +7 , self.rect.y + 10, 1)
            explosion_group.add(explosion)
            #範囲内にダメージ
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
                abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
                player.health -= 30
            for enemy in enemy_group:
                if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
                    abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
                    enemy.health -= 65               


class Explosion(pg.sprite.Sprite):
    def __init__(self,x,y,scale):
        pg.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1,6):
            img = pg.image.load(f'img/explosion/exp{num}.png').convert_alpha()
            img = pg.transform.scale(img, (int(img.get_width()*scale), int(img.get_height()*scale)))
            self.images.append(img)
        self.frame_index = 0    
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x,y)
        self.counter = 0

    def update(self):
        #スクロール
        self.rect.x += screen_scroll    

        EXPLOSION_SPEED = 4
        self.counter += 1

        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]


#画面のフェードアウト
class ScreenFade():
    def __init__(self, direction, colour, speed):
        self.direction = direction
        self.colour = colour
        self.speed = speed
        self.fade_counter = 0

    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1:
            pg.draw.rect(screen, self.colour, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pg.draw.rect(screen, self.colour, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
            pg.draw.rect(screen, self.colour, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
            pg.draw.rect(screen, self.colour, (0, SCREEN_HEIGHT // 2 + self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.direction == 2:
            pg.draw.rect(screen, self.colour, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True

        return fade_complete    


#フェードアウト
intro_fade = ScreenFade(1, BLACK, 6)
death_fade = ScreenFade(2, BLACK, 6)


#ボタン作成
exit_button = button.Button(SCREEN_WIDTH // 7 , SCREEN_HEIGHT // 2, exit_img, 8)
start_button = button.Button(SCREEN_WIDTH // 6 + 300, SCREEN_HEIGHT // 2, start_img, 9)
restart_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 50, restart_img, 9)


#グループ化
enemy_group = pg.sprite.Group()
bullet_group = pg.sprite.Group()
bomb_group = pg.sprite.Group()
explosion_group = pg.sprite.Group() 
item_box_group = pg.sprite.Group()
decoration_group = pg.sprite.Group()
water_group = pg.sprite.Group()
exit_group = pg.sprite.Group()

world_data = []
for row in range(ROWS):
    r = [-1] * COLS
    world_data.append(r)
#レベルのロード、マップの生成
with open(f'level{level}_data.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)    
world = World()
player, health_bar = world.process_data(world_data)



run = True
while run:

    clock.tick(FPS)

    if start_game == False:
        #メインメニュー
        screen.blit(title_img, (0, 0))
        #ボタンの追加
        if start_button.draw(screen):
            start_game = True
            start_intro = True
        if exit_button.draw(screen):
            run = False        
    else:
        #バックグラウンド更新
        draw_bg()
        #ステージの生成
        world.draw()
        #体力の表示
        health_bar.draw(player.health)
        #弾数表示
        draw_text(f'AMMO:{player.ammo}', font, WHITE, 10, 35)
        for x in range(player.ammo):
            screen.blit(bullet_img, (120 + (x * 10), 40))#bullet_img,(x,y)yは要修正
        #爆弾の数
        draw_text(f'BOMB:{player.bombs}', font, WHITE, 10, 60)
        for x in range(player.bombs):
            screen.blit(bomb_img, (135 + (x * 10), 45))#bomb_img,(x,y)yは要修正


        player.update()
        player.draw()

        for enemy in enemy_group:
            enemy.ai()
            enemy.update()
            enemy.draw()
        
        bullet_group.update()
        bomb_group.update()
        explosion_group.update()
        item_box_group.update()
        decoration_group.update() 
        water_group.update() 
        exit_group.update()                 
        bullet_group.draw(screen)
        bomb_group.draw(screen)
        explosion_group.draw(screen)
        item_box_group.draw(screen)
        decoration_group.draw(screen)
        water_group.draw(screen)
        exit_group.draw(screen)                     


        if start_intro == True:
            if intro_fade.fade():
                start_intro = False
                intro_fade.fade_counter = 0


        if player.alive:
            #弾発射
            if shoot:
                player.shoot()
            #爆弾投擲
            elif bomb and bomb_thrown == False and player.bombs > 0:
                bomb = Bomb(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),\
                                player.rect.top,player.direction)
                bomb_group.add(bomb)
                #爆弾減らす
                player.bombs -= 1           
                bomb_thrown = True
            elif player.in_air:
                player.update_action(2)#2：ジャンプ
            elif moving_left or moving_right:
                player.update_action(1)#１：移動
            else:
                player.update_action(0)#0：待機    
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
            #ステージクリア
            if level_complete:
                start_intro = True
                level += 1
                bg_scroll = 0
                world_data = restert_level()
                if level <= MAX_LEVELS:
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)    
                    world = World()
                    player, health_bar = world.process_data(world_data)                                    

        else:
            screen_scroll = 0
            if death_fade.fade():#死亡時のフェードアウト
                if restart_button.draw(screen):
                    death_fade.fade_counter = 0
                    start_intro = True
                    bg_scroll = 0
                    world_data = restert_level()
                    with open(f'level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)    
                    world = World()
                    player, health_bar = world.process_data(world_data)                


    for event in pg.event.get():
        if event.type == pg.QUIT:#ゲーム終了
            run = False
        #キーが押された場合   
        if event.type == pg.KEYDOWN:
            if  event.key == pg.K_a:
                moving_left = True
            if  event.key == pg.K_d:
                moving_right = True
            if  event.key == pg.K_q:
                bomb = True                
            if  event.key == pg.K_SPACE:
                shoot = True                
            if  event.key == pg.K_w and player.alive:
                player.jump = True
                jump_fx.play()
            if event.key == pg.K_ESCAPE:
                run = False    

        #キーが離された場合   
        if event.type == pg.KEYUP:
            if  event.key == pg.K_a:
                moving_left = False
            if  event.key == pg.K_d:
                moving_right = False
            if  event.key == pg.K_SPACE:
                shoot = False  
            if  event.key == pg.K_q:
                bomb = False
                bomb_thrown = False                       

    pg.display.update()                

pg.quit()            