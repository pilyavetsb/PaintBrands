import requests
import time
import ast
import datetime
import codecs
import json


with open ("token.txt",'r') as f:
    token=f.read()

with open("Offset.txt", 'r') as f:
    offsets = ast.literal_eval(f.read())

print(offsets)

version='5.78'
gr_name = 'kraski_dulux'
groups = {'Dulux': 'kraski_dulux', 'Teks': 'tekspaint', 'Pinotex&Hammerite': 'ph_dacha', 'Lacos': 'vincentdecor',
          'Yarkraski': 'yarkraski_ru', 'Parade': 'parade_for_you'}
resolved_groups = {'Lakra': '41596571', 'Tikkurila': '52213494', 'Teksturol': '41596870'}

# Функция для превращения screen name типа "tikkurilaru" в id, необходимо для корректной работы execute
def get_ids(short_name):
    response = requests.get('https://api.vk.com/method/utils.resolveScreenName', params = {'screen_name': short_name, 'access_token': token, 'v': '5.78'}, verify = False)
    time.sleep(0.5)
    return str(response.json()['response']['object_id'])

# Создаем словарь, где каждому бренду соответствует id группы
for key in groups:
    resolved_groups[key] = get_ids(groups[key])

def get_posts_count(group_id):
    response = requests.get('https://api.vk.com/method/wall.get', params = {'owner_id': "-"+group_id, 'access_token': token, 'v': version, 'count': '1'}, verify = False)
    time.sleep(0.5)
    return response.json()['response']['count']

for_offsets = dict()
offset_params = dict()
posts=dict()
for key in resolved_groups:
    for_offsets[key] = get_posts_count(resolved_groups[key])
    posts[key] = []
    if (for_offsets[key]-offsets[key])!=0:
        offset_params[key] = for_offsets[key]-offsets[key]


def get_posts_inc(group_id):
    response = requests.get('https://api.vk.com/method/wall.get', params = {'owner_id': "-"+resolved_groups[group_id],
                                                                            'access_token': token,
                                                                            'v': version,
                                                                            'count': str(offset_params[group_id])}, verify = False)
    time.sleep(0.5)
    return response.json()['response']['items']



posts=dict()
for key in offset_params:
    posts[key] = get_posts_inc(key)
    entry = posts[key]
    res=[]
    for i in entry:
        item = {'id': i['id'], 'comments': i['comments']['count'], 'likes': i['likes']['count'],
                'reposts': i['reposts']['count'],
                'text': i['text'], 'date': 25569 + int(i['date']) / 86400}
        res.append(item)

    posts[key] = res

with open('Offset.txt', 'w'):
    pass

with codecs.open ('Offset.txt','w', 'utf-8') as out:
    out.write(json.dumps(for_offsets, sort_keys=True, ensure_ascii=False))


with codecs.open('Posts.txt', 'r', 'utf-8') as f:
    old = json.load(f)
    for i in old:
        print(i)
        if posts[i]:
            old[i]=old[i]+ posts[i]

with open('Posts.txt','w'):
     pass

with codecs.open('Posts.txt','w', 'utf-8') as f:
    f.write(json.dumps(old, sort_keys=True, ensure_ascii=False))
