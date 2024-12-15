from gpiozero import Button, LED
from smbus2 import SMBus
from i2c_lcd_raspi4 import I2cLcd
from time import sleep, time
from random import randint

# Button control
button = Button(18)

# LEDs
standby_led = LED(15)
victory_led = LED(13)
death_led = LED(12)

# LCD
I2C_ADDR = 0x27
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16
bus = SMBus(1)
lcd = I2cLcd(bus, I2C_ADDR, I2C_NUM_ROWS, I2C_NUM_COLS)
lcd.clear()

# Functions
def lobby():
    lcd.clear()
    lcd.move_to(1, 0)
    lcd.putstr("Press to play")
    lcd.move_to(1, 1)
    lcd.putstr("Highscore: " + str(highscore))
    while not button.is_pressed:
        standby_led.on()
        sleep(0.1)
    standby_led.off()
    lcd.clear()

def move_player_pos(player_pos_y):
    return 1 if player_pos_y == 0 else 0

def choose_obstacle_pos_y():
    return randint(0, 1)

def move_obstacle(score, player_pos_x, obstacle_pos_x, obstacle_pos_y):
    if obstacle_pos_x <= player_pos_x:
        obstacle_pos_y = choose_obstacle_pos_y()
        score += 1
        return 15, obstacle_pos_y, score  # Reset to the right side and increase score
    else:
        obstacle_pos_x -= 1
        return obstacle_pos_x, obstacle_pos_y, score

def check_highscore(score, highscore):
    with open('highscore.txt', 'w') as file:
        file.write(str(max(score, highscore)))
    return max(score, highscore)

def check_death(player_pos_x, player_pos_y, obstacle_pos_x, obstacle_pos_y):
    if player_pos_x == obstacle_pos_x and player_pos_y == obstacle_pos_y:
        lcd.clear()
        lcd.move_to(3, 0)
        lcd.putstr("Game Over!")
        lcd.move_to(3, 1)
        lcd.putstr("Score: " + str(score))
        for _ in range(3):
            death_led.on()
            sleep(1)
            death_led.off()
            sleep(0.5)
        main()  # Restart the game

def check_victory(score, highscore):
    if score >= 100:
        sleep(1)
        lcd.clear()
        lcd.move_to(4, 0)
        lcd.putstr("You Won!")
        lcd.move_to(3, 1)
        lcd.putstr("Score: " + str(score))
        for _ in range(3):
            victory_led.on()
            sleep(1)
            victory_led.off()
            sleep(0.5)
        main()  # Restart the game

# Variables
try:
    with open('highscore.txt', 'r') as file:
        highscore = int(file.read())
except FileNotFoundError:
    highscore = 0

score = 0
player_pos_x = 7
player_pos_y = 0
obstacle_pos_x = 15
obstacle_pos_y = choose_obstacle_pos_y()
interval = time()  # Start time
interval_limit = 0.3  # Time interval for moving the obstacle | initially 0.3 seconds

# Main Game Function
def main():
    global score, highscore, player_pos_x, player_pos_y, obstacle_pos_x, obstacle_pos_y, interval, interval_limit
    obstacle = "o"
    player = "+"
    score_label = "CS:"
    highscore_label = "HS:"
    interval_limit = 0.3
    score = 0
    player_pos_x = 7
    player_pos_y = 0
    obstacle_pos_x = 15
    obstacle_pos_y = choose_obstacle_pos_y()
    lobby()

    while True:
        lcd.move_to(0, 0)
        lcd.putstr(score_label + str(score).ljust(6))
        lcd.move_to(0, 1)
        lcd.putstr(highscore_label + str(highscore).ljust(6))

        lcd.move_to(6, 0)
        lcd.putstr("|")
        lcd.move_to(6, 1)
        lcd.putstr("|")

        lcd.move_to(player_pos_x, player_pos_y)
        lcd.putstr(player)

        lcd.move_to(obstacle_pos_x, obstacle_pos_y)
        lcd.putstr(obstacle)

        # Move the player when the button is pressed
        if button.is_pressed:
            player_pos_y = move_player_pos(player_pos_y)
            lcd.move_to(player_pos_x, player_pos_y)
            lcd.putstr(player)
            sleep(0.15)  # small delay to debounce

        # Move the obstacles after the interval
        if time() - interval >= interval_limit:
            interval = time()  # Reset the interval timer
            interval_limit = max(interval_limit - 0.001, 0.1)  # Increase speed of obstacles over time
            obstacle_pos_x, obstacle_pos_y, score = move_obstacle(score, player_pos_x, obstacle_pos_x, obstacle_pos_y)
            lcd.clear()  # Clear the screen to refresh the obstacle and player positions

        check_death(player_pos_x, player_pos_y, obstacle_pos_x, obstacle_pos_y)
        highscore = check_highscore(score, highscore)
        check_victory(score, highscore)

# Start Game
main()
