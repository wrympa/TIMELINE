from time import sleep

import pygame
import sys
import asyncio
import threading
import os

from service.CardDAO import CardDAO

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from service.ClientService import ClientService


class LoginQueueApp:
    def __init__(self):
        self.detailed_card = None
        self.cardDAO = CardDAO()
        self.selected_card = None
        self.position_input = ""
        self.player_card_rects = []
        self.position_input_rect = None
        self.make_move_rect = None
        self.game_state = None
        self.game_over_timer_set = False
        self.deck_scroll_offset = 0
        pygame.init()
        self.clientService = ClientService(True)

        # Screen setup
        self.screen_width = 1600
        self.screen_height = 900
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("CARD GAME")

        # Colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (200, 200, 200)
        self.LIGHT_BLUE = (173, 216, 230)
        self.GREEN = (100, 200, 100)

        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.mini_font = pygame.font.Font(None, 18)

        # Input fields
        self.username_input = ""
        self.password_input = ""
        self.confirm_password_input = ""
        self.active_input = None

        # Screen states
        self.current_screen = "login"  # "login", "register", "queue", "game"

        # Queue system
        self.queue_position = None

        # Login screen elements
        self.username_rect = pygame.Rect(250, 250, 300, 40)
        self.password_rect = pygame.Rect(250, 350, 300, 40)
        self.login_button_rect = pygame.Rect(300, 450, 200, 50)
        self.register_button_rect = pygame.Rect(300, 520, 200, 40)

        # Register screen elements
        self.reg_username_rect = pygame.Rect(250, 200, 300, 40)
        self.reg_password_rect = pygame.Rect(250, 280, 300, 40)
        self.confirm_password_rect = pygame.Rect(250, 360, 300, 40)
        self.submit_register_rect = pygame.Rect(300, 440, 200, 50)
        self.back_button_rect = pygame.Rect(300, 510, 200, 40)

        # Queue screen buttons
        self.enter_queue_rect = pygame.Rect(250, 250, 300, 50)
        self.quit_button_rect = pygame.Rect(250, 350, 300, 50)

        # Status message
        self.status_message = ""
        self.status_color = self.BLACK

        # Clock for controlling frame rate
        self.clock = pygame.time.Clock()

        # Create an asyncio event loop for the thread
        self.loop = asyncio.new_event_loop()

    def draw_login_screen(self):
        self.screen.fill(self.WHITE)

        # Title
        title = self.title_font.render("Login", True, self.BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(title, title_rect)

        # Username input
        pygame.draw.rect(self.screen, self.GRAY, self.username_rect, 2)
        username_text = self.font.render("Username:", True, self.BLACK)
        self.screen.blit(username_text, (250, 220))
        username_surface = self.font.render(self.username_input, True, self.BLACK)
        self.screen.blit(username_surface, (self.username_rect.x + 10, self.username_rect.y + 10))

        # Password input
        pygame.draw.rect(self.screen, self.GRAY, self.password_rect, 2)
        password_text = self.font.render("Password:", True, self.BLACK)
        self.screen.blit(password_text, (250, 320))
        # Render password as dots
        password_surface = self.font.render("*" * len(self.password_input), True, self.BLACK)
        self.screen.blit(password_surface, (self.password_rect.x + 10, self.password_rect.y + 10))

        # Login button
        pygame.draw.rect(self.screen, self.LIGHT_BLUE, self.login_button_rect)
        login_button_text = self.font.render("Login", True, self.BLACK)
        login_button_rect = login_button_text.get_rect(center=self.login_button_rect.center)
        self.screen.blit(login_button_text, login_button_rect)

        # Register button
        pygame.draw.rect(self.screen, self.GREEN, self.register_button_rect)
        register_button_text = self.small_font.render("Create New Account", True, self.BLACK)
        register_button_rect = register_button_text.get_rect(center=self.register_button_rect.center)
        self.screen.blit(register_button_text, register_button_rect)

        # Status message (for login errors)
        if self.status_message:
            status_text = self.small_font.render(self.status_message, True, self.status_color)
            status_rect = status_text.get_rect(center=(self.screen_width // 2, 410))
            self.screen.blit(status_text, status_rect)

    def draw_register_screen(self):
        self.screen.fill(self.WHITE)

        # Title
        title = self.title_font.render("Create New Account", True, self.BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, 120))
        self.screen.blit(title, title_rect)

        # Username input
        pygame.draw.rect(self.screen, self.GRAY, self.reg_username_rect, 2)
        username_text = self.font.render("Username:", True, self.BLACK)
        self.screen.blit(username_text, (250, 170))
        username_surface = self.font.render(self.username_input, True, self.BLACK)
        self.screen.blit(username_surface, (self.reg_username_rect.x + 10, self.reg_username_rect.y + 10))

        # Password input
        pygame.draw.rect(self.screen, self.GRAY, self.reg_password_rect, 2)
        password_text = self.font.render("Password:", True, self.BLACK)
        self.screen.blit(password_text, (250, 250))
        # Render password as dots
        password_surface = self.font.render("*" * len(self.password_input), True, self.BLACK)
        self.screen.blit(password_surface, (self.reg_password_rect.x + 10, self.reg_password_rect.y + 10))

        # Confirm Password input
        pygame.draw.rect(self.screen, self.GRAY, self.confirm_password_rect, 2)
        confirm_password_text = self.font.render("Confirm Password:", True, self.BLACK)
        self.screen.blit(confirm_password_text, (250, 330))
        # Render confirm password as dots
        confirm_password_surface = self.font.render("*" * len(self.confirm_password_input), True, self.BLACK)
        self.screen.blit(confirm_password_surface,
                         (self.confirm_password_rect.x + 10, self.confirm_password_rect.y + 10))

        # Register button
        pygame.draw.rect(self.screen, self.GREEN, self.submit_register_rect)
        register_button_text = self.font.render("Register", True, self.BLACK)
        register_button_rect = register_button_text.get_rect(center=self.submit_register_rect.center)
        self.screen.blit(register_button_text, register_button_rect)

        # Back button
        pygame.draw.rect(self.screen, self.LIGHT_BLUE, self.back_button_rect)
        back_button_text = self.small_font.render("Back to Login", True, self.BLACK)
        back_button_rect = back_button_text.get_rect(center=self.back_button_rect.center)
        self.screen.blit(back_button_text, back_button_rect)

        # Status message (for registration errors/success)
        if self.status_message:
            status_text = self.small_font.render(self.status_message, True, self.status_color)
            status_rect = status_text.get_rect(center=(self.screen_width // 2, 400))
            self.screen.blit(status_text, status_rect)

    def draw_queue_screen(self):
        self.screen.fill(self.WHITE)

        # Title
        title = self.title_font.render("Welcome to the card game", True, self.BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, 150))
        self.screen.blit(title, title_rect)
        title = self.font.render(f"you are logged in as {self.clientService.currName}", True, self.BLACK)
        title_rect = title.get_rect(center=(self.screen_width // 2, 200))
        self.screen.blit(title, title_rect)

        # Enter Queue button
        pygame.draw.rect(self.screen, self.LIGHT_BLUE, self.enter_queue_rect)
        enter_queue_text = self.font.render("Enter Queue", True, self.BLACK)
        enter_queue_rect = enter_queue_text.get_rect(center=self.enter_queue_rect.center)
        self.screen.blit(enter_queue_text, enter_queue_rect)

        # Quit button
        pygame.draw.rect(self.screen, (255, 100, 100), self.quit_button_rect)
        quit_text = self.font.render("Quit", True, self.BLACK)
        quit_rect = quit_text.get_rect(center=self.quit_button_rect.center)
        self.screen.blit(quit_text, quit_rect)

        # Display queue position if entered
        if self.clientService.queueWaitingStatus != "":
            queue_text = self.font.render(f"{self.clientService.queueWaitingStatus}", True,
                                          self.BLACK)
            queue_rect = queue_text.get_rect(center=(self.screen_width // 2, 500))
            self.screen.blit(queue_text, queue_rect)

        # Only switch to game if we're not coming from a game over state
        # and game address is available
        if self.clientService.gameAddrs != "" and not self.game_over_timer_set:
            self.current_screen = "game"

    def draw_game_screen(self):
        self.screen.fill(self.WHITE)

        # === Title ===
        title = self.title_font.render("Card Game", True, self.BLACK)
        self.screen.blit(title, title.get_rect(center=(self.screen_width // 2, 30)))

        if not hasattr(self, 'game_state') or not self.game_state:
            status_text = self.font.render("Waiting for game data...", True, self.BLACK)
            self.screen.blit(status_text,
                             status_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2)))
            return

        # Check if we're showing a detailed card view
        if hasattr(self, 'detailed_card') and self.detailed_card is not None:
            self.draw_detailed_card_view()
            return

        y_offset = 70  # Start below the title

        # === Game Status ===
        if self.game_state.get("over", False):
            game_over_text = self.font.render("Game Over!", True, (255, 0, 0))
            self.screen.blit(game_over_text, game_over_text.get_rect(center=(self.screen_width // 2, y_offset)))
            y_offset += 40
            if not self.game_over_timer_set:
                pygame.time.set_timer(pygame.USEREVENT + 1, 5000)
                self.game_over_timer_set = True
        else:
            turn_text = self.font.render(f"Current Turn: Player {self.game_state['currentTurn']}", True, self.BLACK)
            self.screen.blit(turn_text, turn_text.get_rect(center=(self.screen_width // 2, y_offset)))
            y_offset += 40

        # === Deck (Scrollable) ===
        deck_title = self.font.render("Deck:", True, self.BLACK)
        self.screen.blit(deck_title, deck_title.get_rect(midleft=(50, y_offset)))

        y_offset += 30  # Extra spacing to avoid overlap with cards

        self.deck_card_rects = []  # Store deck card rectangles for click detection

        deck_x_start = 120 - self.deck_scroll_offset
        for i, card_idx in enumerate(self.game_state["deck"]):
            card_rect = pygame.Rect(deck_x_start + i * 200, y_offset, 150, 240)
            pygame.draw.rect(self.screen, self.LIGHT_BLUE, card_rect)
            pygame.draw.rect(self.screen, self.BLACK, card_rect, 2)

            self.deck_card_rects.append((card_rect, card_idx))

            # Card Number
            realCard = self.cardDAO.getNthCard(card_idx)
            title = realCard.title
            if len(title) > 15:
                title = title[: 15] + "..."
            card_text = self.small_font.render(title, True, self.BLACK)
            self.screen.blit(card_text, card_text.get_rect(center=card_rect.center))

            mid_x_prev = deck_x_start + i * 200 - 25  # Midpoint between this card and the next
            mid_x_next = deck_x_start + (i+1) * 200 - 25  # Midpoint between this card and the next
            placement_text_prev = self.small_font.render(str(i), True, self.BLACK)
            placement_text_next = self.small_font.render(str(i + 1), True, self.BLACK)
            self.screen.blit(placement_text_prev, (mid_x_prev, y_offset + 250))  # Just below the cards
            self.screen.blit(placement_text_next, (mid_x_next, y_offset + 250))  # Just below the cards

        y_offset += 300  # Ensure space before opponents

        # === Opponents ===
        player_id = self.clientService.currName
        opponents = [p for p in self.game_state["hands"].keys() if p != player_id]

        for i, opp_id in enumerate(opponents[:3]):
            opp_y = y_offset + (i * 120)  # Adjusted spacing to avoid overlap
            points = self.game_state["points"][opp_id]
            name_color = self.GREEN if self.game_state["currentTurn"] == opp_id else self.BLACK

            opp_name = self.font.render(f"Player {opp_id}: {points} pts", True, name_color)
            self.screen.blit(opp_name, opp_name.get_rect(midleft=(50, opp_y)))

            card_start_x = 200
            for j in range(len(self.game_state["hands"][opp_id])):
                card_rect = pygame.Rect(card_start_x + j * 30, opp_y + 30, 25, 50)
                pygame.draw.rect(self.screen, (100, 100, 200), card_rect)
                pygame.draw.rect(self.screen, self.BLACK, card_rect, 1)

        # === Player Area (Shifted to Bottom Right) ===
        player_points = self.game_state["points"][player_id]
        player_name_color = self.GREEN if self.game_state["currentTurn"] == player_id else self.BLACK

        player_stats_x = self.screen_width / 2  # Shift to right side
        player_stats_y = self.screen_height - 400  # Move up

        # Player Name & Points
        player_name = self.font.render(f"You ({player_id}): {player_points} pts", True, player_name_color)
        self.screen.blit(player_name, player_name.get_rect(midleft=(player_stats_x, player_stats_y)))

        # Player Cards (Centered Above Input)
        card_width = 120
        card_height = 180
        player_cards = self.game_state["hands"][player_id]
        total_width = len(player_cards) * (card_width + 10)
        start_x = player_stats_x - total_width // 2  # Center within the stats area

        self.player_card_rects = []

        for i, card_idx in enumerate(player_cards):
            card_rect = pygame.Rect(start_x + i * card_width + 10, player_stats_y + 40, card_width, card_height)
            self.player_card_rects.append((card_rect, card_idx))

            pygame.draw.rect(self.screen, (255, 255, 0) if self.selected_card == i else self.LIGHT_BLUE, card_rect)
            pygame.draw.rect(self.screen, self.BLACK, card_rect, 2)

            realCard = self.cardDAO.getNthCard(card_idx)
            title = realCard.title
            if len(title) > 15:
                title = title[: 15] + "..."
            card_text = self.mini_font.render(title, True, self.BLACK)
            self.screen.blit(card_text, card_text.get_rect(center=card_rect.center))

        # === Input & Button (Below Player Cards) ===
        pileSize_x = self.screen_width - 300
        pileSize_y = self.screen_height - 100

        player_name = self.font.render(f"Cards left in pile: {self.game_state['pileSize']}", True, self.BLACK)
        self.screen.blit(player_name, player_name.get_rect(midleft=(pileSize_x, pileSize_y)))

        input_x = player_stats_x + 20
        input_y = self.screen_height - 130

        # Text Input for Index
        self.position_input_rect = pygame.Rect(input_x, input_y, 100, 40)
        pygame.draw.rect(self.screen, self.GRAY, self.position_input_rect, 2)
        position_text_surface = self.font.render(self.position_input, True, self.BLACK)
        self.screen.blit(position_text_surface, (self.position_input_rect.x + 10, self.position_input_rect.y + 10))

        # "Make Move" Button
        self.make_move_rect = pygame.Rect(input_x, input_y + 50, 150, 40)
        button_color = self.LIGHT_BLUE if self.game_state["currentTurn"] == player_id else self.GRAY
        pygame.draw.rect(self.screen, button_color, self.make_move_rect)
        move_text = self.font.render("Make Move", True, self.BLACK)
        self.screen.blit(move_text, move_text.get_rect(center=self.make_move_rect.center))

    def draw_detailed_card_view(self):
        """Draws a detailed view of a card with title, description, and image"""
        # Semi-transparent background
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))

        # Get card details
        card = self.cardDAO.getNthCard(self.detailed_card)

        # Card container
        card_width = self.screen_width * 0.6
        card_height = self.screen_height * 0.7
        card_x = (self.screen_width - card_width) / 2
        card_y = (self.screen_height - card_height) / 2

        card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
        pygame.draw.rect(self.screen, self.WHITE, card_rect)
        pygame.draw.rect(self.screen, self.BLACK, card_rect, 3)

        # Card title
        title_y = card_y + 20
        card_title = self.title_font.render(card.title, True, self.BLACK)
        self.screen.blit(card_title, card_title.get_rect(center=(self.screen_width // 2, title_y)))

        # Card image (assuming card has an image attribute or method to get image)
        image_height = card_height * 0.5
        image_rect = pygame.Rect(card_x + 20, title_y + 50, card_width - 40, image_height)

        # If the card has an image loaded, use it; otherwise use a placeholder
        if hasattr(card, 'index') and card.index:
            try:
                image = pygame.image.load(f"../cardImages/{card.index}.png")
            except FileNotFoundError:
                image = pygame.image.load(f"../cardImages/{card.index}.jpg")
            image = pygame.transform.scale(image, (card_width - 40, image_height))
            self.screen.blit(image, image_rect)
        else:
            print(f"../cardImages/{card.index}.png")
            pygame.draw.rect(self.screen, self.LIGHT_BLUE, image_rect)
            img_text = self.font.render("Card Image", True, self.BLACK)
            self.screen.blit(img_text, img_text.get_rect(center=image_rect.center))

        # Card description (with text wrapping)
        desc_y = image_rect.bottom + 20
        description = card.descr if hasattr(card, 'descr') else "No description available."

        # Simple text wrapping
        words = description.split()
        lines = []
        current_line = []
        font_width = self.font.size("A")[0]  # Approximate width of a character
        max_chars = int((card_width - 40) / font_width)

        for word in words:
            if len(" ".join(current_line + [word])) <= max_chars:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        for i, line in enumerate(lines):
            desc_text = self.font.render(line, True, self.BLACK)
            self.screen.blit(desc_text, (card_x + 20, desc_y + i * 30))

        # Close button
        close_btn_width = 100
        close_btn_height = 40
        close_btn_x = self.screen_width // 2 - close_btn_width // 2
        close_btn_y = card_y + card_height - close_btn_height - 20

        self.close_btn_rect = pygame.Rect(close_btn_x, close_btn_y, close_btn_width, close_btn_height)
        pygame.draw.rect(self.screen, self.LIGHT_BLUE, self.close_btn_rect)
        pygame.draw.rect(self.screen, self.BLACK, self.close_btn_rect, 2)

        close_text = self.font.render("Close", True, self.BLACK)
        self.screen.blit(close_text, close_text.get_rect(center=self.close_btn_rect.center))

    # This function runs the coroutine in a separate thread
    def run_async_coroutine(self, coroutine):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(coroutine)

    def handle_registration(self):
        """Process the registration request"""
        # Validate inputs
        if not self.username_input or not self.password_input or not self.confirm_password_input:
            self.status_message = "All fields are required"
            self.status_color = (255, 0, 0)  # Red for error
            return

        if self.password_input != self.confirm_password_input:
            self.status_message = "Passwords do not match"
            self.status_color = (255, 0, 0)  # Red for error
            return

        if len(self.password_input) < 4:
            self.status_message = "Password must be at least 4 characters"
            self.status_color = (255, 0, 0)  # Red for error
            return

        # Send registration request
        parts = ["REG", self.username_input, self.password_input]
        registration_success = self.clientService.attemptRegister(parts)

        if registration_success:
            self.status_message = "Registration successful! You can now login."
            self.status_color = (0, 128, 0)  # Green for success
            # Auto-switch back to login after a short delay
            pygame.time.set_timer(pygame.USEREVENT, 2000)  # 2 seconds delay
        else:
            self.status_message = "Registration failed. Username may already exist."
            self.status_color = (255, 0, 0)  # Red for error

    def make_move(self, card_idx, position):
        """Send the move to the server"""
        # Validate that it's the player's turn
        player_id = self.clientService.currName
        if self.game_state["currentTurn"] != player_id:
            self.status_message = "Not your turn!"
            self.status_color = (255, 0, 0)  # Red for error
            return

        print("TRYING")
        print("lel", card_idx, [position])
        self.clientService.recieveMoveFromVisuals(card_idx, [position])
        print("SUCCING")

        # Clear selection and input after move
        self.selected_card = None
        self.position_input = ""
        self.active_input = None
        self.status_message = "Move sent!"
        self.status_color = self.GREEN

    def run(self):
        running = True
        # Custom events
        auto_switch_event = pygame.USEREVENT
        game_over_event = pygame.USEREVENT + 1

        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == auto_switch_event:
                    if self.current_screen == "register" and "successful" in self.status_message:
                        self.current_screen = "login"
                        pygame.time.set_timer(auto_switch_event, 0)  # Disable the timer
                elif event.type == game_over_event:
                    if self.game_state and self.game_state.get("over", False):
                        self.current_screen = "queue"
                        pygame.time.set_timer(game_over_event, 0)  # Disable the timer
                        self.game_over_timer_set = False  # Reset the flag
                        self.clientService.gameAddrs = ""  # Clear the game address
                        self.game_state = None  # Clear the game state
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_mouse_click(event.pos)
                elif event.type == pygame.KEYDOWN:
                    self.handle_key_press(event)

            # Draw appropriate screen
            if self.current_screen == "login":
                self.draw_login_screen()
            elif self.current_screen == "register":
                self.draw_register_screen()
            elif self.current_screen == "queue":
                self.draw_queue_screen()
            elif self.current_screen == "game":
                # Only update game state if not in game over state
                if not self.game_over_timer_set:
                    self.game_state = self.clientService.get_game_state()
                self.draw_game_screen()

            # Update display
            pygame.display.flip()

            # Control frame rate
            self.clock.tick(60)

        # Clean up
        if self.loop.is_running():
            self.loop.stop()
        pygame.quit()
        sys.exit()

    def handle_mouse_click(self, pos):
        """Handle mouse click events based on current screen"""
        if self.current_screen == "login":
            # Username input field
            if self.username_rect.collidepoint(pos):
                self.active_input = "username"
            # Password input field
            elif self.password_rect.collidepoint(pos):
                self.active_input = "password"
            # Login button
            elif self.login_button_rect.collidepoint(pos):
                if not self.username_input or not self.password_input:
                    self.status_message = "Please enter both username and password"
                    self.status_color = (255, 0, 0)  # Red for error
                else:
                    parts = ["LOG", self.username_input, self.password_input]
                    logged_in = self.clientService.attemptAuth(parts)
                    if logged_in:
                        self.status_message = ""
                        self.current_screen = "queue"
                    else:
                        self.status_message = "Login failed. Check your credentials."
                        self.status_color = (255, 0, 0)  # Red for error
            # Register button
            elif self.register_button_rect.collidepoint(pos):
                self.current_screen = "register"
                self.status_message = ""
                # Clear password fields when switching to register
                self.password_input = ""
                self.confirm_password_input = ""
            else:
                self.active_input = None

        elif self.current_screen == "register":
            # Username input field
            if self.reg_username_rect.collidepoint(pos):
                self.active_input = "username"
            # Password input field
            elif self.reg_password_rect.collidepoint(pos):
                self.active_input = "password"
            # Confirm Password input field
            elif self.confirm_password_rect.collidepoint(pos):
                self.active_input = "confirm_password"
            # Register button
            elif self.submit_register_rect.collidepoint(pos):
                self.handle_registration()
            # Back button
            elif self.back_button_rect.collidepoint(pos):
                self.current_screen = "login"
                self.status_message = ""
            else:
                self.active_input = None

        elif self.current_screen == "queue":
            # Enter Queue button
            if self.enter_queue_rect.collidepoint(pos):
                # Run the async function in a separate thread
                threading.Thread(
                    target=self.run_async_coroutine,
                    args=(self.clientService.attemptEnqueue(),)
                ).start()
            # Quit button
            elif self.quit_button_rect.collidepoint(pos):
                pygame.quit()
                sys.exit()

        elif self.current_screen == "game" and not self.game_over_timer_set:
            # Only handle game clicks if the game is not over
            # Check if a card was clicked
            mouse_pos = pygame.mouse.get_pos()
            if hasattr(self, 'detailed_card') and self.detailed_card is not None:
                # Check if close button clicked in detail view
                if hasattr(self, 'close_btn_rect') and self.close_btn_rect.collidepoint(mouse_pos):
                    self.detailed_card = None
            else:
                # Check for card clicks in regular view
                # Check player's cards
                for rect, card_idx in self.player_card_rects:
                    if rect.collidepoint(mouse_pos):
                        self.detailed_card = card_idx
                        break

                # Check deck cards
                if hasattr(self, 'deck_card_rects'):
                    for rect, card_idx in self.deck_card_rects:
                        if rect.collidepoint(mouse_pos):
                            self.detailed_card = card_idx
                            break

                # Check make move button click
                if hasattr(self, 'make_move_rect') and self.make_move_rect.collidepoint(mouse_pos):
                    if self.game_state["currentTurn"] == self.clientService.currName:
                        try:
                            position = int(self.position_input)
                            if self.selected_card is not None:
                                self.make_move(self.selected_card, position)
                        except ValueError:
                            pass

            phys_list_index = 0
            for card_rect, card_idx in self.player_card_rects:
                if card_rect.collidepoint(pos) and self.detailed_card is not None:
                    self.selected_card = phys_list_index
                    break
                phys_list_index += 1

            if self.position_input_rect and self.position_input_rect.collidepoint(pos):
                self.active_input = "position"
            elif self.make_move_rect and self.make_move_rect.collidepoint(pos):
                if self.selected_card is not None and self.position_input:
                    try:
                        position = int(self.position_input)
                        self.make_move(self.selected_card, position)
                    except ValueError:
                        self.status_message = "Please enter a valid position number"
                        self.status_color = (255, 0, 0)
            else:
                if not any(rect[0].collidepoint(pos) for rect in self.player_card_rects):
                    self.active_input = None

    def handle_key_press(self, event):
        """Handle keyboard events"""
        if event.key == pygame.K_LEFT:  # Scroll left
            self.deck_scroll_offset = max(0, self.deck_scroll_offset - 60)
        elif event.key == pygame.K_RIGHT:  # Scroll right
            self.deck_scroll_offset += 60  # Move right
        if hasattr(self, 'detailed_card') and self.detailed_card is not None:
            # Close detailed view on ESC key
            if event.key == pygame.K_ESCAPE:
                self.detailed_card = None
        elif event.key == pygame.K_TAB:
            # Handle tab key for input field navigation
            if self.current_screen == "login":
                if self.active_input == "username":
                    self.active_input = "password"
                elif self.active_input == "password":
                    self.active_input = "username"
            elif self.current_screen == "register":
                if self.active_input == "username":
                    self.active_input = "password"
                elif self.active_input == "password":
                    self.active_input = "confirm_password"
                elif self.active_input == "confirm_password":
                    self.active_input = "username"
            elif self.current_screen == "game":
                if self.active_input == "position":
                    self.active_input = None
                else:
                    self.active_input = "position"

        elif event.key == pygame.K_RETURN:
            if self.current_screen == "login":
                if not self.username_input or not self.password_input:
                    self.status_message = "Please enter both username and password"
                    self.status_color = (255, 0, 0)
                else:
                    parts = ["LOG", self.username_input, self.password_input]
                    logged_in = self.clientService.attemptAuth(parts)
                    if logged_in:
                        self.status_message = ""
                        self.current_screen = "queue"
                    else:
                        self.status_message = "Login failed. Check your credentials."
                        self.status_color = (255, 0, 0)
            elif self.current_screen == "register":
                self.handle_registration()
            elif self.current_screen == "game" and self.active_input == "position" and not self.game_over_timer_set:
                if self.selected_card is not None and self.position_input:
                    try:
                        position = int(self.position_input)
                        self.make_move(self.selected_card, position)
                    except ValueError:
                        self.status_message = "Please enter a valid position number"
                        self.status_color = (255, 0, 0)

        elif event.key == pygame.K_BACKSPACE:
            if self.active_input == "username":
                self.username_input = self.username_input[:-1]
            elif self.active_input == "password":
                self.password_input = self.password_input[:-1]
            elif self.active_input == "confirm_password":
                self.confirm_password_input = self.confirm_password_input[:-1]
            elif self.active_input == "position":
                self.position_input = self.position_input[:-1]

        elif self.active_input:
            if self.active_input == "username":
                self.username_input += event.unicode
            elif self.active_input == "password":
                self.password_input += event.unicode
            elif self.active_input == "confirm_password":
                self.confirm_password_input += event.unicode
            elif self.active_input == "position" and event.unicode.isdigit():
                self.position_input += event.unicode


def main():
    app = LoginQueueApp()
    app.run()


if __name__ == "__main__":
    main()
