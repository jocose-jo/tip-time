import random

horse_map = {
    "horse_brown": 1116114371446317100,
    "horse_blue": 1116123670683848775,
    "horse_gold": 1116123557253107832,
    "horse_orange": 1116123586911027240,
    "horse_pink": 1116123685267447859,
    "horse_purple": 1116123641244028998,
    "horse_teal": 1116123571991892059,
}


def get_random_unique_horses(amount):
    horses = [{"name": name, "id": horse_id} for name, horse_id in horse_map.items()]
    return random.sample(horses, amount)

