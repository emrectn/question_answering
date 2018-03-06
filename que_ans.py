from html.parser import HTMLParser
from enum import Enum
from pprint import pprint
import json


# def find_similarty_sentence(text_list, question):
#     equal_word_number = []
#     counter = 0

#     question = question.replace()
#     question = question.split()
#     for question_word in question


def tr_lower(str):
    rep = [('İ', 'i'),  ('I', 'ı')]
    for search, replace in rep:
        str = str.replace(search, replace)
        return str.lower()

# metni cumlelere gore ayirma fonksiyonu
def sentence_parser(data_content):
    # data_content = metin ve sorulari
    # data_text = metinin cumleleri '.' ya gore ayrilarak listeye kaydedildi.

    data_text = data_content['metin'].split(".")
    # Metin cumlelerin basinda ve sonundaki bosluklarin silinmesi
    for i, sentence in enumerate(data_text):
        data_text[i] = sentence.strip()

    return data_text


def find_answer(text, question):
    #cevap cumlesinin, kontrol icin diz
    common_word_numbers = []

    for text_sentence in text:
        common_word_numbers.append(calc_common_word(text_sentence, question))
    #    print(common_word_numbers)
    index = common_word_numbers.index(max(common_word_numbers))
    return text[index]


# ortak kelime sayisini bulur
def calc_common_word(text_sentence, question):
    # ortak kelime sayisini tutar
    common = 0
    # kucuk harfe cevirme, bosluga gore parcalama, gereksiz bosluk silinmesi
    text_sentence = tr_lower(text_sentence).strip().split()
    question = tr_lower(question).strip().split()

    for question_word in question:
        if question_word in text_sentence:
            common += 1
    return common


class DataStatus(Enum):
    TEXT = 0
    QUESTION = 1
    ANSWER = 2
    EMPTY = -1


class MyHTMLParser(HTMLParser):
    def __init__(self, *args, **kwargs):
        super(MyHTMLParser, self).__init__(*args, **kwargs)
        self.data_status = DataStatus.EMPTY
        self.data = []
    # Datanin metin, soru, cevap oldugunu belirlemize yarar.

    def handle_starttag(self, tag, attrs):
        if 'metin' in tag:
            self.data_status = DataStatus.TEXT
            # print('Bu bir metin {}'.format(DataStatus.TEXT.name))

        elif 'soru' in tag:
            self.data_status = DataStatus.QUESTION

        elif 'cevap' in tag:
            self.data_status = DataStatus.ANSWER

        else:
            print('Metin parcalanirken hata oluÅŸtu')

        # print("start tag:", tag.strip())

    def handle_data(self, data):
        # metinin baÅŸÄ±ndaki ve sonunda '\n'den kurtuluyoruz.
        # data_content = data.strip()
        # re.sub('\n', '', data_content)
        data_content = data.replace('\n', ' ').strip()
        if self.data_status == DataStatus.TEXT:
            self.data.append({'metin': data_content, 'sorular': []})
        elif self.data_status == DataStatus.QUESTION:
            self.data[-1]['sorular'].append({'soru': data_content})
        elif self.data_status == DataStatus.ANSWER:
            self.data[-1]['sorular'][-1]['cevap'] = data_content
            self.data[-1]['sorular'][-1]['bulunan_cevap'] = ''

    # metni cumlelere gore ayirma fonksiyonu        self.data[-1]['sorular'][-1]['status'] = ''

if __name__ == '__main__':
    with open('data-set.txt') as f:
        metin = f.read()
    parser = MyHTMLParser()
    parser.feed(metin)

    # pprint(parser.data)
    with open('data.json', 'w') as f:
        json.dump(parser.data, f, indent=4)

    data = parser.data

    for data_content in data:
        text_sentences = sentence_parser(data_content)
        question_list = data_content['sorular']
        for question in question_list:
            question['bulunan_cevap'] = find_answer(text_sentences, question['soru'])
            print('soru:', question['soru'])
            print('dogru:', question['cevap'])
            print('cevap:', question['bulunan_cevap'])
            input('')