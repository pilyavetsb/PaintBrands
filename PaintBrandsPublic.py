import requests
import time
import datetime
import codecs
import json


with open ("token.txt",'r') as f:
    token=f.read()

version='5.78'
gr_name = 'kraski_dulux'
pers_token = '36a0bb07a18fb16e7dfd893ec19170e602b10899caa561a3297e3f43d7ac26912da5a82ab3596dc3c36e3'
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

print(resolved_groups)
#получаем кол-во участников в каждой группе, понадобится для выкачивания подробных данных по участникам, т.к. вконтакте позволяет забирать не более 25000 участников за раз
def get_members_count(group_id):
    response = requests.get('https://api.vk.com/method/groups.getMembers', params = {'group_id': group_id, 'access_token': token, 'v': version, 'count': '1'}, verify = False)
    time.sleep(0.5)
    return response.json()['response']['count']

#записываем в словарь кол-во участников в соответствии с брендом и инициализируем словарь, где будет хранится инфа по участникам
members=dict()
membersGroup = dict()
for key in resolved_groups:
    members[key]=get_members_count(resolved_groups[key])
    membersGroup[key] = []

#получаем всех участников с доп. информацией - делаем через execute, чтобы можно было вытащить сразу 25000, а не по 1000 тягать.
#Сначала первый проход, а потом цикл, пока всех участников не вытащим
def get_members(group_id, key):
    global membersGroup
    code = 'var members_count=API.groups.getMembers({group_id: ' + group_id + ',v:5.78, sort:"id_asc", fields:["sex","bdate","city","country"], count:1000, offset:' + str(len(membersGroup[key]))+'}).items;' \
                           'var offset=1000;' \
                           'while (offset<25000 && (offset + ' + str(len(membersGroup[key]))+') <' +str(members[key])+') ' \
                                        '{members_count=members_count + API.groups.getMembers({' \
                                        'group_id: ' + group_id + ',v:5.78, sort:"id_asc", count:1000, fields:["sex","bdate","city","country"], offset: (' + str(len(membersGroup[key]))+'+offset)}).items;' \
                                        'offset = offset+1000;};' \
                                        'return members_count;'
    response=requests.get('https://api.vk.com/method/execute', params={'code':code, 'access_token':pers_token, 'v':version}, verify=False)
    membersGroup[key]=membersGroup[key]+response.json()['response']
    time.sleep(0.5)
    while len(membersGroup[key]) < members[key]:
        get_members(group_id,key)
    return membersGroup[key]

members_fin = dict()
for key in resolved_groups:
    members_fin[key] = get_members(resolved_groups[key], key)

def get_posts_count(group_id):
    response = requests.get('https://api.vk.com/method/wall.get', params = {'owner_id': "-"+group_id, 'access_token': token, 'v': version, 'count': '1'}, verify = False)
    time.sleep(0.5)
    return response.json()['response']['count']

posts = dict()
posts_w_text_temp = dict()
for key in resolved_groups:
    posts[key] = get_posts_count(resolved_groups[key])
    posts_w_text_temp[key] = []


def get_posts(key):
    global posts_w_text_temp
    code = 'var posts_count=API.wall.get({owner_id: -' + resolved_groups[key] + ', v:5.78, count:50, offset:'+ str(len(posts_w_text_temp[key])) + '}).items;' \
           ' var offset = 50;' \
           ' while (offset<1250 &&(offset+'+str(len(posts_w_text_temp[key])) + ')<' + str(posts[key]) + ')' \
           '    {posts_count=posts_count+API.wall.get({owner_id: -' + resolved_groups[key] + ', v:5.78, count:50, offset: offset+' + str(len(posts_w_text_temp[key])) + '}).items;' \
           ' offset=offset+50;};' \
           ' return posts_count;'
    response = requests.get('https://api.vk.com/method/execute', params={'code':code, 'access_token':pers_token, 'v':version}, verify=False)
    posts_w_text_temp[key] = posts_w_text_temp[key] + response.json()['response']
    time.sleep(0.5)
    while len(posts_w_text_temp[key]) < posts[key]:
        get_posts(key)
    return posts_w_text_temp

posts_w_text = dict()
for key in resolved_groups:
    print(key)
    get_posts(key)

posts_final=dict()
for key in resolved_groups:
    entry=posts_w_text_temp[key]
    res=[]
    for i in entry:
        item = {'id': i['id'],'comments':i['comments']['count'], 'likes': i['likes']['count'], 'reposts': i['reposts']['count'],
                        'text': i['text'],'date': 25569 + int(i['date'])/86400}
        if 'views' in i:
            item['views'] = i['views']['count']
        else:
            item['views'] = ""
        res.append(item)
    posts_final[key] = res


#clearing file from previous version
with open('Posts.txt','w'):
    pass

#writing data to a blank file
with codecs.open('Posts.txt', 'w', 'utf-8') as outfile:
    outfile.write(json.dumps(posts_final, ensure_ascii=False, sort_keys=True))

#clearing file from previous version
with open ('Members.txt', 'w'):
    pass

#writing data to a blank file
with codecs.open('Members.txt','w', 'utf-8') as out:
    out.write(json.dumps(membersGroup,ensure_ascii=False, sort_keys=True))