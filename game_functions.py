import sys
import pygame
from time import sleep
from bullet import Bullet
from alien import Alien
import json


def write_file(stats):
    with open('files/hs_file.txt', 'w') as file:
        json.dump(stats.high_score, file)


def read_file(stats):
    with open('files/hs_file.txt', 'r') as file:
        stats.high_score = json.load(file)


def get_number_aliens_x(ai_settings, alien_width):
    available_space_x = ai_settings.screen_width - 2 * alien_width
    number_aliens_x = int(available_space_x / (2 * alien_width))
    return number_aliens_x


def get_number_rows(ai_settings, ship_height, alien_height):
    available_space_y = (ai_settings.screen_height - 3 * alien_height - ship_height)
    number_rows = int(available_space_y / (2 * alien_height))
    return number_rows


def create_alien(ai_settings, screen, aliens, alien_number, row_number):
    alien = Alien(ai_settings, screen)
    alien_width = alien.rect.width
    alien.x = alien_width + 2 * alien_width * alien_number
    alien.rect.x = alien.x
    alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
    aliens.add(alien)


def create_fleet(ai_settings, screen, ship, aliens):
    alien = Alien(ai_settings, screen)
    number_aliens_x = get_number_aliens_x(ai_settings, alien.rect.width)
    number_rows = get_number_rows(ai_settings, ship.rect.height, alien.rect.height)
    for row_number in range(number_rows):
        for alien_number in range(number_aliens_x):
            create_alien(ai_settings, screen, aliens, alien_number, row_number)


def check_play_button(stats, play_button, mouse_x, mouse_y, aliens, bullets, ship, ai_settings, screen, sb):
    """Start a new game when the player clicks Play"""
    button_clicked = play_button.rect.collidepoint(mouse_x, mouse_y)
    if button_clicked and not stats.game_active:
        # Read from hs_file.txt the high_score
        read_file(stats)
        # Reset the game settings.
        ai_settings.initialize_dynamic_settings()
        # Hide the mouse cursor.
        pygame.mouse.set_visible(False)
        # Reset the game statistics.
        stats.reset_stats()
        stats.game_active = True
        sb.prep_score()
        sb.prep_high_score()
        sb.prep_level()
        sb.prep_ships()

        aliens.empty()
        bullets.empty()
        create_fleet(ai_settings, screen, ship, aliens)
        ship.center_ship()


def fire_bullet(ai_settings, screen, ship, bullets):
    if len(bullets) < ai_settings.bullets_allowed:
        new_bullet = Bullet(ai_settings, screen, ship)
        bullets.add(new_bullet)


def check_keydown_events(event, ai_settings, screen, ship, bullets):
    if event.key == pygame.K_RIGHT:
        ship.moving_right = True
    if event.key == pygame.K_LEFT:
        ship.moving_left = True
    elif event.key == pygame.K_SPACE:
        # Create new bullet and add it to the bullets group.
        fire_bullet(ai_settings, screen, ship, bullets)


def check_keyup_events(event, ship):
    if event.key == pygame.K_RIGHT:
        ship.moving_right = False
    if event.key == pygame.K_LEFT:
        ship.moving_left = False


def check_events(ai_settings, screen, ship, bullets, stats, play_button, aliens, sb):
    # Respond to keypresses and mouse events
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                # Writing high_score to file.
                write_file(stats)
                sys.exit()
        if event.type == pygame.QUIT:
            write_file(stats)
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            check_keydown_events(event, ai_settings, screen, ship, bullets)
        elif event.type == pygame.KEYUP:
            check_keyup_events(event, ship)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            check_play_button(stats, play_button, mouse_x, mouse_y, aliens, bullets, ship, ai_settings, screen, sb)


def ship_hit(ai_settings, stats, screen, ship, aliens, bullets, sb):
    if stats.ships_left > 0:
        write_file(stats)
        stats.ships_left -= 1
        # Update scoreboard.
        sb.prep_ships()
        bullets.empty()
        aliens.empty()
        create_fleet(ai_settings, screen, ship, aliens)
        ship.center_ship()
        sleep(0.5)
    else:
        stats.game_active = False
        pygame.mouse.set_visible(True)


def check_aliens_bottom(ai_settings, stats, screen, ship, aliens, bullets, sb):
    screen_rect = screen.get_rect()
    for alien in aliens.sprites():
        if alien.rect.bottom >= screen_rect.bottom:
            ship_hit(ai_settings, stats, screen, ship, aliens, bullets, sb)
            break


def check_fleet_edges(ai_settings, aliens):
    for alien in aliens.sprites():
        if alien.check_edges():
            change_fleet_direction(ai_settings, aliens)
            break


def change_fleet_direction(ai_settings, aliens):
    for alien in aliens.sprites():
        alien.rect.y += ai_settings.fleet_drop_speed
    ai_settings.fleet_direction *= -1


def check_high_score(stats, sb):
    """Checking for new high-score."""
    if stats.score > stats.high_score:
        stats.high_score = stats.score
        sb.prep_high_score()
        write_file(stats)


def check_bullet_aliens_collisions(ai_settings, screen, ship, aliens, bullets, stats, sb):
    collisions = pygame.sprite.groupcollide(bullets, aliens, True, True)
    if collisions:
        for aliens in collisions.values():
            stats.score += ai_settings.alien_points * len(aliens)
            sb.prep_score()
        check_high_score(stats, sb)
    if len(aliens) == 0:
        # Destroy existing bullets, speed up the game, create new fleet.
        bullets.empty()
        ai_settings.increase_speed()
        create_fleet(ai_settings, screen, ship, aliens)
        # Increase level
        stats.level += 1
        sb.prep_level()


def update_bullets(ai_settings, screen, ship, aliens, bullets, stats, sb):
    """Update position of bullets and get rid of old bullets"""
    # Update bullet positions.
    bullets.update()
    # Get rid of bullets that have disappeared.
    for bullet in bullets.copy():
        if bullet.rect.bottom <= 0:
            bullet.kill()
    check_bullet_aliens_collisions(ai_settings, screen, ship, aliens, bullets, stats, sb)


def update_aliens(ai_settings, stats, screen, ship, aliens, bullets, sb):
    check_fleet_edges(ai_settings, aliens)
    aliens.update()
    if pygame.sprite.spritecollideany(ship, aliens):
        ship_hit(ai_settings, stats, screen, ship, aliens, bullets, sb)
    check_aliens_bottom(ai_settings, stats, screen, ship, aliens, bullets, sb)


def update_screen(ai_settings, screen, sb, ship, bullets, aliens, stats, play_button):
    # Updates images on the screen and flip to the new screen
    screen.fill(ai_settings.bg_color)
    # Redraw all bullets behind ship and aliens.
    # for bullet in bullets.sprites():
    #     bullet.draw_bullet()
    bullets.draw(screen)
    ship.blitme()
    # for a in aliens.sprites():
    #     a.blitme()
    aliens.draw(screen)
    # Draw the play_button if the game is inactive.
    sb.show_score()
    if not stats.game_active:
        play_button.draw_button()
    pygame.display.flip()



