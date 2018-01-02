import hlt
import logging

game = hlt.Game("Mishok_v6b_Planets")
logging.info("Starting my Mishok_v6b_ bot!")

# game_map = game.update_map()

# PLANETS_BY_SIZE = game_map.all_planets().sort(key=lambda planet: planet.radius)
# MAX_PLANET_RADIUS = PLANETS_BY_SIZE[0].radius

def sort_by_dist(obj, lst):
    lst.sort(key=lambda lst_obj: lst_obj.calculate_distance_between(obj))
    return lst

def planets_by_dist(obj, planets_list):
    return sort_by_dist(obj, planets_list)

def planets_by_rating(obj, planets_list):
    PLANETS_BY_SIZE = sort_planets_by_radius(planets_list)
    # print((PLANETS_BY_SIZE[0].radius))
    max_radius = PLANETS_BY_SIZE[0].radius
    planets_list.sort(key=lambda planet: planet.calculate_distance_between(obj)/(planet.radius)*max_radius)
    return planets_list

def enemy_ships(enemies):
    enemies_ships = []
    for player in enemies:
        enemies_ships.extend(player.all_ships())
    return enemies_ships

def enemy_ships_by_dist(obj, enemies):
    enemies_ships = []
    for player in enemies:
        enemies_ships.extend(player.all_ships())
    return sort_by_dist(obj, enemies_ships)

def all_entities_by_dist(obj, planets_list, enemies, max_ships):
    entities = []
    entities.extend(enemy_ships_by_dist(obj, enemies)[:int(max_ships)])
    entities.extend(planets_list)

    return sort_by_dist(obj, entities)

def sort_planets_by_radius(lst):
    lst.sort(key=lambda lst_obj: lst_obj.radius)
    return(lst)

def planet_has_docked_ships(planet):
    return len(planet.all_docked_ships()) > 0

def planet_is_my(planet, my_ships):
    logging.info("my all_docked_ships len " + str(len(planet.all_docked_ships())))
    return planet.all_docked_ships()[0] in my_ships

def attack_miners(ship, planet, game_map):
    return ship.navigate(
        ship.closest_point_to(planet.all_docked_ships()[0], min_distance=1),
        game_map,
        speed=int(hlt.constants.MAX_SPEED),
        max_corrections=3,
        angular_step=2)

def ship_dock_to_planet(ship, planet, game_map):
    if ship.can_dock(planet):
        logging.info("dock")
        return ship.dock(planet)
    else:
        logging.info("nav to planet")
        return ship.navigate(
            ship.closest_point_to(planet),
            game_map,
            speed=int(hlt.constants.MAX_SPEED),
            max_corrections=3,
            angular_step=2)

def all_planets_are_owned(planets):
    for planet in planets:
        if planet.is_owned():
            continue
        else:
            return False
    return True


turn_count = 0
while True:
    turn_count += 1
    game_map = game.update_map()

    # PLANETS_BY_SIZE = sort_planets_by_radius(game_map.all_planets())
    # # print((PLANETS_BY_SIZE[0].radius))
    # max_radius = PLANETS_BY_SIZE[0].radius

    navigate_command = None
    command_queue = []

    me = game_map.get_me()
    my_ships = me.all_ships()

    my_undocked_ships = [ship for ship in my_ships if ship.docking_status != ship.DockingStatus.DOCKED]

    planets = game_map.all_planets()
    
    enemies = game_map.all_players()
    enemies.remove(me)
    enemies_ships = enemy_ships(enemies)

    if len(my_undocked_ships) > len(enemies_ships)/len(enemies)*1.33:
        for ship in my_undocked_ships:
            enemy_ship = sort_by_dist(ship, enemies_ships)[0]
            navigate_command = ship.navigate(
                ship.closest_point_to(enemy_ship, min_distance=1),
                game_map,
                speed=int(hlt.constants.MAX_SPEED),
                max_corrections=3,
                angular_step=2)
        
            if navigate_command:
                command_queue.append(navigate_command)
    else:
        for ship in my_undocked_ships[:30]:
            # logging.info("--in ships--")
            if not all_planets_are_owned(planets):
                nearby_entities = planets_by_rating(ship, planets)
            else:
                nearby_entities = all_entities_by_dist(ship, planets, enemies, 10)

            for entity in nearby_entities:
                # logging.info("in entities")
                if isinstance(entity, hlt.entity.Planet):
                    # logging.info("planet")
                    if planet_has_docked_ships(entity):
                        # logging.info("has docked ships")
                        if planet_is_my(entity, my_ships):
                            # logging.info("my ships")
                            if entity.is_full():
                                # logging.info("full of ships")
                                continue
                            else:
                                # logging.info("not full of ships")
                                navigate_command = ship_dock_to_planet(ship, entity, game_map)
                                if navigate_command:
                                    command_queue.append(navigate_command)
                                    break
                        else:
                            # logging.info("not my ships")
                            navigate_command = attack_miners(ship, entity, game_map)
                            if navigate_command:
                                command_queue.append(navigate_command)
                                break
                    else:
                        # logging.info("has no docked ships")
                        navigate_command = ship_dock_to_planet(ship, entity, game_map)
                        # logging.info("navigate_command = " + str(navigate_command))
                        if navigate_command:
                            command_queue.append(navigate_command)
                            break

                elif isinstance(entity, hlt.entity.Ship) and (entity not in my_ships):
                    if turn_count < 150:
                        continue
                    else:
                        navigate_command = ship.navigate(
                            entity,
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            max_corrections=3,
                            angular_step=2)
                    
                        if navigate_command:
                            command_queue.append(navigate_command)
                            break
                
    if not command_queue:
        # logging.info("empty command_queue")
        game.send_command_queue(command_queue)
    else:
        game.send_command_queue(command_queue)
