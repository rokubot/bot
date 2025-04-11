import random
import re
import textwrap
from io import BytesIO

import discord
import humanize
import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


def rounded_image(avatar):
    avatar = Image.open(avatar).resize((250, 250)).convert('RGBA')
    mask = Image.open('./pics/mask.png').convert('L')
    output = ImageOps.fit(avatar, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)
    output = output.resize((250, 250))
    avatar.close()
    return output


def wanted_poster(data=None):
    avatar = Image.open(data)
    avatar = avatar.resize((512, 512))
    wanted = Image.open("./pics/test.png")
    wanted.paste(avatar, (100, 250))
    avatar.close()
    draw = ImageDraw.Draw(wanted)
    font1 = ImageFont.truetype("./fonts/wanted.ttf", 65)
    price = random.randint(10000, 99999)
    draw.text((48, 770), f"${humanize.intcomma(price)} REWARD!", "black", font=font1)
    final_image = BytesIO()
    wanted.save(final_image, "png")
    final_image.seek(0)
    wanted.close()
    return final_image


def stone(data=None):
    avatar = Image.open(data).convert('L')
    stone = avatar.filter(ImageFilter.SHARPEN).filter(ImageFilter.EMBOSS)
    final_image = BytesIO()
    stone.save(final_image, "png")
    final_image.seek(0)
    avatar.close()
    return final_image


def color_processing(color: discord.Color):
    im = Image.new('RGB', (150, 150), color.to_rgb())
    buff = BytesIO()
    im.save(buff, 'png')
    buff.seek(0)
    im.close()
    return buff


def qrcreate(text):
    qr = qrcode.make(text)
    im = BytesIO()
    qr.save(im, "png")
    im.seek(0)
    qr.close()
    return im


def match_love(user1, user2, percent):
    im = Image.open('./pics/lbg.jpg').convert("RGBA")
    avatar1 = Image.open(user1).resize((210, 210))
    avatar2 = Image.open(user2).resize((210, 210))
    im.paste(avatar1, (0, 0))
    im.paste(avatar2, (410, 0))
    avatar1.close()
    avatar2.close()
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype('./fonts/aller.ttf', 40)
    draw.text((270, 70), f"{percent}%", font=font)
    card = BytesIO()
    im.save(card, "PNG")
    card.seek(0)
    im.close()
    return card


def drake(t1=None, t2=None):
    data = random.randint(1, 4)
    im = Image.open(f"./pics/drake0{data}.png")
    draw = ImageDraw.Draw(im)
    font = ImageFont.truetype("./fonts/LDFComicSans.ttf", 30)
    if len(t1) >= 80:
        t1 = t1[:95]
        text1 = textwrap.fill(t1, width=15)
        draw.text((270, 10), text1, fill="black", font=font)
    else:
        t1 = t1[:95]
        text1 = textwrap.fill(t1, width=14)
        draw.text((280, 70), text1, fill="black", font=font)

    if len(t2) >= 80:
        t2 = t2[:100]
        text1 = textwrap.fill(t2, width=15)
        draw.text((270, 280), text1, fill="black", font=font)
    else:
        t2 = t2[:100]
        text1 = textwrap.fill(t2, width=14)
        draw.text((280, 320), text1, fill="black", font=font)
    done = BytesIO()
    im.save(done, "png")
    done.seek(0)
    im.close()
    return done


def welcome_image(*, avatar, custombg, fontinfo, textcolor, imagetext, textborder, avatarborder) -> BytesIO:
    avatar = rounded_image(avatar)
    im = Image.new('RGBA', (1024, 450))
    im.paste(avatar, (380, 15))
    draw = ImageDraw.Draw(im)
    fontinfo = fontinfo or {'name': 'Antom', 'size': 50, 'location': './fonts/antom.ttf', 'spacing': 2}
    font = ImageFont.truetype(fontinfo['location'], fontinfo['size'])
    draw.ellipse([(397, 30), (613, 240)], outline=avatarborder, width=4)
    draw.multiline_text(
        (510, 300),
        imagetext,
        fill=textcolor,
        stroke_fill=textborder,
        stroke_width=5,
        font=font,
        spacing=fontinfo['spacing'],
        align="center",
        anchor="ms",
    )
    newim = Image.open(custombg).convert('RGBA').resize((1024, 450))
    newim.paste(im, mask=im)
    card = BytesIO()
    newim.save(card, 'PNG')
    card.seek(0)
    avatar.close()
    im.close()
    newim.close()
    return card


def tinder_image(user1, user2):
    bg = Image.open('./pics/tin.png')
    user1 = rounded_image(user1)
    user2 = rounded_image(user2)

    bg.paste(user1, (30, 280))
    bg.paste(user2, (300, 280))

    im = BytesIO()
    bg.save(im, "PNG")
    im.seek(0)
    return im


def letter_replace(num: str):
    letter = {"thousand": "K", "million": "M", "billion": "B", "trillion": "T", "quadrillion": "Q"}

    for n, l in letter.items():
        num = num.replace(n, l)
    return num


status_dict = {'online': '#2ecc71', 'offline': '#747f8d', 'dnd': '#f04747', 'idle': '#faa61a'}


def text_fmt(lvl=0, end_xp=100, xp=0, urrank=1):
    lvl = str(lvl)
    xp = str(lvl)
    urrank = str(urrank)

    lvl_word = (480, 20)
    lvl_pos = (528, 15)
    if len(lvl) > 3:
        lvl_word = (460, 20)
        lvl_pos = (508, 15)

    rank_word = (380, 20)
    rank_pos = (425, 15)
    if (n := len(urrank)) > 2:
        rank_word = (380 - (n * 11), 20)
        rank_pos = (425 - (n * 11), 15)

    res = {'rank_word': rank_word, 'rank_pos': rank_pos, 'lvl_word': lvl_word, 'lvl_pos': lvl_pos}
    return res


def rank_image(user=None, lvl=None, end_xp=None, xp=None, data=None, urrank=4, status='online'):
    data = rounded_image(data)
    im = Image.open('./pics/bar.png').convert('RGB')
    draw = ImageDraw.Draw(im)
    rank = Image.open('./pics/nrank.png')

    color = (255, 129, 192)  # color of the bar.

    bar_fillings = int(xp / end_xp * 600)
    x, y, diam = bar_fillings, 8, 34
    draw.ellipse([x, y, x + diam, y + diam], fill=color)
    ImageDraw.floodfill(im, xy=(14, 24), value=color, thresh=40)
    rank.paste(im.resize((410, 35)), (155, 110))
    rank.paste(data.resize((150, 150)), (3, 8), mask=data.resize((150, 150)))
    draw = ImageDraw.Draw(rank)
    draw.ellipse(
        [(105, 115), (130, 140)], fill=status_dict[status], outline='black', width=3
    )  # online, offline status round

    font1 = ImageFont.truetype("./fonts/Helvetica.ttf", 25)
    font2 = ImageFont.truetype("./fonts/helvetica-light.ttf", 15)

    username, _h, tag = user.rpartition('#')
    bbox = font1.getbbox(username)
    w = bbox[2]

    if len(username) >= 10:
        altfont = ImageFont.truetype("./fonts/Helvetica.ttf", 22)
        draw.text((175, 95), username[:12], "white", font=altfont)
        bbox = altfont.getbbox(username[:12])
        w = bbox[2]
    else:
        draw.text((175, 90), username, "white", font=font1)

    draw.text((180 + w, 95), _h + tag, "white", font=font2)

    fancified_xp = humanize.intword(xp, format='%.0f')
    fancified_exp = humanize.intword(end_xp, format='%.0f')

    string = f"{fancified_xp} / {fancified_exp} XP"
    draw.text((470, 95), f"{letter_replace(string)}", "white", font=font2)

    res = text_fmt(lvl=lvl, end_xp=end_xp, xp=xp, urrank=urrank)

    draw.text(res['lvl_word'], f"LEVEL", color, font=font2)
    draw.text(res['lvl_pos'], str(lvl), color, font=font1)
    draw.text(res['rank_word'], f"RANK", "white", font=font2)
    draw.text(res['rank_pos'], f"#{urrank}", "white", font=font1)

    card = BytesIO()
    rank.save(card, "png")
    card.seek(0)

    data.close()
    im.close()
    rank.close()

    return card
