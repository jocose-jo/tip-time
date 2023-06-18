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


def get_random_unique_horses(bot_emojis, amount):
    filtered_horses = [{"name": emoji.name, "id": emoji.id} for emoji in bot_emojis if emoji.id in horse_map.values()]
    return random.sample(filtered_horses, amount)


def trim_name(name: str, length: int):
    if len(name) < length:
        return name.ljust(length)
    return name[0:length]