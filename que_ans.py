from html.parser import HTMLParser
from difflib import SequenceMatcher
from enum import Enum
from pprint import pprint
from ngram import NGram
from pyfasttext import FastText
import os
import re
import math
import json
import string


N_GRAM = 3
WORD_SIZE = 6
VECTOR_NUM = 300
# Gordugu karakterleri digeriyle degistiriyor
TO_LOWER = str.maketrans('ABCÇDEFGĞHIIJKLMNOÖPQRSŞTUÜVWXYZ',
                         'abcçdefgğhıijklmnoöpqrsştuüvwxyz',
                         '’“”')


# Kosinüs benzerliği hesaplanır.
def cosine_similarity(v1, v2):
    "compute cosine similarity of v1 to v2: (v1 dot v2)/{||v1||*||v2||)"
    sumxx, sumxy, sumyy = 0, 0, 0

    if len(v1) != len(v2):
        print('Vektörler aynı uzayda değil')
        return None

    for i in range(len(v1)):
        x = v1[i]
        y = v2[i]
        sumxx += x*x
        sumyy += y*y
        sumxy += x*y
    return sumxy/math.sqrt(sumxx*sumyy)


# Bir cümle icersindeki noktalama işaretlerini kaldıran fonksiyon
def remove_punctuation(sentence):
    exclude = set(string.punctuation)
    sentence = ''.join(ch for ch in sentence if ch not in exclude)
    return sentence


# iki cümle karsilastirilarak cümlelerin esit olup olmadıgı kontrol edilir.
def is_answer_true(answer, finding_answer):
    answer = answer.replace('.', '').strip()
    answer = tr_lower(answer)

    finding_answer = finding_answer.replace('.', '').strip()
    finding_answer = tr_lower(finding_answer)

    ratio = SequenceMatcher(None, answer, finding_answer).ratio()
    if ratio == 1.0:
        return True
    else:
        return False


# Dogru_cümle_sayisi/Toplam_cümle_sayisi oranını hesaplar
def success_rate(data):
    total = 0
    successful = 0

    for data_content in data:
        for question in data_content['sorular']:
            if question['status']:
                successful += 1
            total += 1

    return (successful/total)*100


# Turkce karakterler icin ozel lower fonksiyonu
def tr_lower(s):
    return s.translate(TO_LOWER)


# metni cumlelere gore ayirma fonksiyonu
def sentence_parser(data_content):
    # data_content = metin ve sorulari
    # data_text = metinin cumleleri '.' ya gore ayrilarak listeye kaydedildi.

    data_text = data_content['metin'].split(".")
    # Metin cumlelerin basinda ve sonundaki bosluklarin silinmesi
    for i, sentence in enumerate(data_text):
        data_text[i] = sentence.strip()

    # Bosluk varsa kaldırılıyor.
    if '' in data_text:
        data_text.remove('')
    return data_text


def find_answer_index(text, question, mode):
    # cevap cumlesinin, kontrol icin diz
    common_word_numbers = []

    if mode == 0:
        for text_sentence in text:
            common_word_numbers.append(calc_common_word(
                                        text_sentence, question))

    elif mode == 1:
        for text_sentence in text:
            common_word_numbers.append(calc_common_word_sixch(
                                        text_sentence, question))

    elif mode == 2:
        for text_sentence in text:
            common_word_numbers.append(calc_common_word_ngram(
                                        text_sentence, question))
    else:
        print('Mode hatasi')

    #    print(common_word_numbers)
    index = int(common_word_numbers.index(max(common_word_numbers)))
    return index


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


def calc_common_word_sixch(text_sentence, question):
    common = 0

    # Noktalama isaretlerinden temizlendi
    text_sentence = remove_punctuation(text_sentence)
    question = remove_punctuation(question)

    # Kucuk harf ve kelime kelime parcalama islemi
    text_sentence = tr_lower(text_sentence).strip().split()
    question = tr_lower(question).strip().split()

    # ilk 6 harfin alınması
    text_sentence = edit_length_word(text_sentence, WORD_SIZE)
    question = edit_length_word(question, WORD_SIZE)

    # Ortak kelime karsilastrilmasi
    for question_word in question:
        if question_word in text_sentence:
            common += 1
    return common


# ngram kullanarak ortak kelime sayisinin hesaplanmasi
def calc_common_word_ngram(text_sentence, question):
    common = 0

    # Noktalama isaretlerinden temizlendi
    text_sentence = remove_punctuation(text_sentence)
    question = remove_punctuation(question)

    # Kucuk harf ve kelime kelime parcalama islemi
    text_sentence = tr_lower(text_sentence).strip()
    question = tr_lower(question).strip()

    n = NGram(N=N_GRAM)
    list_text_sentence = list(n.split(text_sentence))
    list_question = list(n.split(question))

    # print(list_text_sentence)
    # print()
    # print(list_question)
    # input('')

    for question_word in list_question:
        if question_word in list_text_sentence:
            # print(question_word)
            common += 1

    return common


def edit_length_word(word_list, word_length):
    # İlk WORD_SIZE harfin alinmasi
    for i, sentence_word in enumerate(word_list):
        if len(sentence_word) > WORD_SIZE:
            word_list[i] = word_list[i][0:word_length]
            # print(word_list[i])
    return word_list


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
            print('Metin parcalanirken hata oluştu')

        # print("start tag:", tag.strip())

    def handle_data(self, data):
        # metinin basindaki ve sonunda '\n'den kurtuluyoruz.
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
            self.data[-1]['sorular'][-1]['status'] = ''


if __name__ == '__main__':
    with open('data-set.txt') as f:
        metin = f.read()
    parser = MyHTMLParser()
    parser.feed(metin)

    # pprint(parser.data)
    with open('data.json', 'w') as f:
        json.dump(parser.data, f, indent=4)

    data = parser.data

    # İki yöntem icin for dongusu donmektedir.
    for i in range(3):
        for data_content in data:
            text_sentences = sentence_parser(data_content)
            question_list = data_content['sorular']

            for question in question_list:
                    answer_index = find_answer_index(text_sentences, question['soru'], i)

                    if isinstance(answer_index, int):
                        question['bulunan_cevap'] = text_sentences[answer_index]
                    else:
                        print('İndex Bulunamadi')

                    if is_answer_true(question['cevap'], question['bulunan_cevap']):
                        question['status'] = True
                    else:
                        question['status'] = False

                    # print('Cevap : ', question['cevap'])
                    # print('MY : ', question['bulunan_cevap'])
                    # print('Sonuc : ', question['status'])
                    # print()


        # pprint(parser.data)
        with open('data' + str(i) + '.json', 'w') as f:
            json.dump(parser.data, f, indent=4)
        if i == 0:
            print('Kelime kelime karşılaştırma')
        elif i == 1:
            print('İlk 6 harf karşılaştırma')
        else:
            print('Ngram bazlı karşılaştırma')
        print(' Basari Orani-{} : {}\n'.format(i, success_rate(data)))


# -----------------------------------------------------------------

    for data_content in data:
        print(data_content)
        input('')
        text_sentence = sentence_parser(data_content)
        print(text_sentence)
        input('')

        question_list = data_content['sorular']
        print(question_list)
        input('')

        for question in question_list:
            print(question)
            input('')
