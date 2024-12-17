from gpiozero import Button, LED
from RPLCD.i2c import CharLCD
from time import sleep, time
from random import randint

# Button and LEDs
button = Button(18, pull_up=True)  # GPIO18
standby_led = LED(15)  # GPIO15
victory_led = LED(13)  # GPIO13
death_led = LED(12)    # GPIO12

# LCD setup
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=2, charmap='A00')
lcd.clear()

# Functions
def lobby():
    lcd.clear()
    lcd.cursor_pos = (0, 1)
    lcd.write_string("Press to play")
    lcd.cursor_pos = (1, 1)
    lcd.write_string(f"Highscore: {highscore}")
    while button.is_pressed is False:
        standby_led.on()
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
        lcd.cursor_pos = (0, 3)
        lcd.write_string("Game Over!")
        lcd.cursor_pos = (1, 3)
        lcd.write_string(f"Score: {score}")
        for _ in range(3):
            death_led.on()
            sleep(1)
            death_led.off()
            sleep(0.5)
        main()

def check_victory(score, highscore):
    if score >= 100:
        sleep(1)
        lcd.clear()
        lcd.cursor_pos = (0, 4)
        lcd.write_string("You Won!")
        lcd.cursor_pos = (1, 3)
        lcd.write_string(f"Score: {score}")
        for _ in range(3):
            victory_led.on()
            sleep(1)
            victory_led.off()
            sleep(0.5)
        main()

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
start_time = time()
interval_limit = 0.3  # Interval for moving the obstacle (seconds)

# Main Game Function
def main():
    global score, highscore, player_pos_x, player_pos_y, obstacle_pos_x, obstacle_pos_y, start_time, interval_limit
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
        lcd.clear()
        lcd.cursor_pos = (0, 0)
        lcd.write_string(f"{score_label}{score}")
        lcd.cursor_pos = (1, 0)
        lcd.write_string(f"{highscore_label}{highscore}")
        
        lcd.cursor_pos = (0, 6)
        lcd.write_string("|")
        lcd.cursor_pos = (1, 6)
        lcd.write_string("|")
        
        lcd.cursor_pos = (player_pos_y, player_pos_x)
        lcd.write_string(player)
        
        lcd.cursor_pos = (obstacle_pos_y, obstacle_pos_x)
        lcd.write_string(obstacle)
        
        # Move the player when the button is pressed
        if button.is_pressed:
            player_pos_y = move_player_pos(player_pos_y)
            sleep(0.15)  # Small delay to debounce
        
        # Move the obstacle after the interval
        if time() - start_time >= interval_limit:
            start_time = time()
            interval_limit = max(interval_limit - 0.01, 0.1)  # Increase speed, limit to 0.1s
            obstacle_pos_x, obstacle_pos_y, score = move_obstacle(score, player_pos_x, obstacle_pos_x, obstacle_pos_y)
        
        check_death(player_pos_x, player_pos_y, obstacle_pos_x, obstacle_pos_y)
        highscore = check_highscore(score, highscore)
        check_victory(score, highscore)

# Start Game
main()
