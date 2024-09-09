import os
import shutil

import cv2
from pyzbar.pyzbar import decode
import glob
import yoshium

"""
　議決権行使書のQRコード面の画像を「imgフォルダ」内、「PNG形式」に格納する。
　画像スキャンする場合は、白黒400dpi程度だと失敗が少ない。

　　(注意)
　　　画像ファイル名に空白が入っているとエラーかも。

　以下に、株主の情報を書き込む。
==============================================
"""

MAIL_ADDRESS = '***+*@gmail.com'
BIRTH_YEAR = '1985' # 西暦4桁、半角数字
SEX = '女性' # '男性' or '女性'
# 投資経験年数
#  1年未満
#  1～3年程度
#  4～6年程度
#  7～9年程度
#  10年以上
EXPERIENCE = '10年以上'
# 職業（下記から選択）
#  会社員・公務員
# 学生
# 専業主婦
# パート
PROFESSION = '会社員'

"""
==============================================
株主情報、ここまで
"""

# FILE_IMG_HEIC = 'img/IMG_0122.HEIC'
# FILE_IMG_PNG = "img/image2.png"
#
# def conv_to_png(heic_img):
#     """
#     HEIC画像をPNG画像に変換し保存する
#     :param heic_img: HEIC画像
#     :return: None
#     """
#     heif_file = pillow_heif.open_heif(heic_img, convert_hdr_to_8bit=False, bgr_mode=True)
#     np_array = np.asarray(heif_file)
#
#     file_name = heic_img.replace('.HEIC', '.png')
#     cv2.imwrite(file_name, np_array)

def get_data_qrdec(file_img_png):

    img_bgr = cv2.imread(file_img_png, cv2.IMREAD_COLOR)

    decoded_list = decode(img_bgr)

    # 画像の表示
    # img_resized = cv2.resize(img_bgr, None, fx=0.2, fy=0.2)
    # cv2.imshow('image', img_resized)
    # cv2.waitKey(0)

    # TODO QRコードが読み取れなかった場合、読めなかったコードの画像を表示する？

    list_data = []
    for d in decoded_list:
        list_data.append(d.data.decode())

    return list_data

def get_url(list_str):
    """
    文字列リストの要素から最初に見つかったURLを返す
    :param list_str:
    :return:
    """
    for s in list_str:
        if s.startswith('http'):
            return s
    return None

def del_space(str_text):
    """
    空白文字等を削除し、句点の直後で改行を行う
    :param str_text:
    :return: 加工後の文字列
    """
    str_text = str_text.replace('\n', '')
    str_text = str_text.replace('\t', '')
    str_text = str_text.replace(' ', '')
    str_text = str_text.replace('。', '。\n')
    return str_text

def giketuken_koushi(ys, url):
    """
    議決権行使とアンケート回答を行う
    :param ys: Yoshiumオブジェクト
    :param url: URL文字列
    :return:
    """
    # 議決権サイトにアクセス
    ys.go_to(url)

    def koushi_smtphn_site(ys=ys):
        # Beautifulsoupオブジェクトの生成
        soup = ys.cook_soup()

        # 銘柄名
        meigara_name = soup.select_one('body > header > div:nth-child(3) > div > p.text-l.top')
        if meigara_name:
            print(meigara_name.text)
        # 総会開催日
        date_soukai = soup.select_one('body > header > div:nth-child(3) > div > p:nth-child(2)')
        if date_soukai:
            print(date_soukai.text)

        # 期限が過ぎている場合
        cls_info = soup.find("p", {"class": "guidance end-info"})
        if cls_info:
            # 空白文字等を削除
            str_info = del_space(cls_info.text)
            print(str_info)
            return

        # 既に議決権行使を行っている場合
        cls_info = soup.find("p", {"class": "guidance info"})
        if cls_info:
            # 空白文字等を削除
            str_info = del_space(cls_info.text)
            print(str_info)

        else:
            # 「すべての会社提案議案について賛成」
            elem_btn = ys.elem_id('enter')
            ys.click(elem_or_str=elem_btn)
            yoshium.wait()

            # 「この内容で行使する」
            elem_btn = ys.elem_selector('#MainForm > div.button_do.set2 > button')
            ys.click(elem_or_str=elem_btn)
            yoshium.wait()

            # 「行使受付完了」
            elem_info = ys.elem_selector('body > header > p.title.subtitle')
            if elem_info:
                print(elem_info.text)
                elem_info = ys.elem_selector('body > header > p.guidance-non')
                if elem_info:
                    elem_info = del_space(elem_info.text)
                    print(elem_info)
                yoshium.wait()

        # ここにアンケートがある場合あり
        # 「アンケートに回答する」
        elem_info = ys.elem_selector('#MainForm > p')
        if elem_info:
            str_info = elem_info.text
            str_info = del_space(str_info)
            if 'アンケート等へご回答いただいております' in str_info:
                return
        elem_enquete = ys.elem_id('enquete')
        if elem_enquete:
            ys.click(elem_or_str=elem_enquete)
            yoshium.wait()
        else:
            elem_enquete = ys.elems_selector('#question')
            if elem_enquete is not None and 1 < len(elem_enquete):
                ys.click(elem_or_str=elem_enquete[1])
                yoshium.wait()
            else:
                # ボタンが1つしかない →　「議決権を再行使する」ボタンのみ
                # アンケートは無い
                return

        if elem_enquete:
            # =======================
            # アンケートページ
            # =======================

            # 1. 性別
            elem_dropdown = ys.elem_id('_EDN1SUB0IDX1.1')
            if elem_dropdown:
                ys.elem_dropdown_select(elem=elem_dropdown, num_select="2")
            else:
                elem_radio = ys.elem_selector('#MainForm > div.question-list > section:nth-child(1) > div > p:nth-child(2) > label')
                if elem_radio:
                    ys.click(elem_radio)

            # 2. 年齢
            elem_dropdown = ys.elem_id('_EDN2SUB0IDX1.1')
            if elem_dropdown:
                ys.elem_dropdown_select(elem=elem_dropdown, num_select="3")

            # 3. 職業 / 保有株式数
            elem_dropdown = ys.elem_id('_EDN3SUB0IDX1.1')
            if elem_dropdown:
                ys.elem_dropdown_select(elem=elem_dropdown, num_select="2")

            # 電子提供制度について
            elem_check = ys.elem_selector('#MainForm > div.question-list > section:nth-child(4) > div > p:nth-child(1) > label')
            if elem_check:
                ys.click(elem_check)

            # 株主総会資料について
            elem_check = ys.elem_selector(
                '#MainForm > div.question-list > section:nth-child(5) > div > p:nth-child(1) > label')
            if elem_check:
                ys.click(elem_check)

            # 議決権行使について
            elem_check = ys.elem_selector(
                '#MainForm > div.question-list > section:nth-child(6) > div > p:nth-child(1) > label')
            if elem_check:
                ys.click(elem_check)

            # 総会資料閲覧ウェブサイトについて
            elem_check = ys.elem_selector(
                '#MainForm > div.question-list > section:nth-child(7) > div > p:nth-child(1) > label')
            if elem_check:
                ys.click(elem_check)
            elem_check = ys.elem_selector(
                '#MainForm > div.question-list > section:nth-child(7) > div > p:nth-child(6) > label')
            if elem_check:
                ys.click(elem_check)

            # 8.「使おう！スマート行使キャンペーン」に応募するか
            elem_dropdown = ys.elem_id('_EDN8SUB0IDX1.1')
            if elem_dropdown:
                ys.elem_dropdown_select(elem=elem_dropdown, num_select="1")

            # 4. 保有年数
            elem_dropdown = ys.elem_id('_EDN4SUB0IDX1.1')
            if elem_dropdown:
                ys.elem_dropdown_select(elem=elem_dropdown, num_select="1")

            # 8. 投資検討
            elem_radio = ys.elem_selector('#MainForm > div.question-list > section:nth-child(8) > div > p:nth-child(2) > label')
            if elem_radio:
                ys.click(elem_radio)

            # プレゼント企画に応募するか
            elem_radio = ys.elem_selector('#MainForm > div.question-list > section:nth-child(9) > div > p:nth-child(1) > label')
            if elem_radio:
                ys.click(elem_radio)

            # 9. 保有年数
            elem_dropdown = ys.elem_id('_EDN9SUB0IDX1.1')
            if elem_dropdown:
                ys.elem_dropdown_select(elem=elem_dropdown, num_select="6")

            # 10. 方針
            elem_dropdown = ys.elem_id('_EDN10SUB0IDX1.1')
            if elem_dropdown:
                ys.elem_dropdown_select(elem=elem_dropdown, num_select="5")

            # 11. 投資金額
            elem_dropdown = ys.elem_id('_EDN11SUB0IDX1.1')
            if elem_dropdown:
                ys.elem_dropdown_select(elem=elem_dropdown, num_select="5")

            # 12. サマリー版招集通知
            elem_dropdown = ys.elem_id('_EDN12SUB0IDX1.1')
            if elem_dropdown:
                ys.elem_dropdown_select(elem=elem_dropdown, num_select="1")

            # 回答の確認
            input('- アンケートの確認 (press Enter to next)')

            # 入力確認する
            elem_btn = ys.elem_id('btn')
            ys.click(elem_btn)
            yoshium.wait()

            # 送信する
            elem_btn = ys.elem_id('btn')
            ys.click(elem_btn)
            yoshium.wait()

            # （アンケート）「受付完了」
            elem_info = ys.elem_selector('body > header > p.title.noline')
            if elem_info:
                print(elem_info.text)
                elem_info = ys.elem_selector('body > main > p')
                elem_info = del_space(elem_info.text)
                print(elem_info)
                yoshium.wait()

    def koushi_evoting_site(ys=ys):
        # Beautifulsoupオブジェクトの生成
        soup = ys.cook_soup()

        # 銘柄名
        meigara_name = soup.select_one('#page > form > table.kaigyou > tbody > tr > td > b > font')
        if meigara_name:
            print(meigara_name.text)
        # 総会開催日
        date_soukai = soup.select_one('#page > form > table:nth-child(3) > tbody > tr:nth-child(2) > td > font')
        if date_soukai:
            print(date_soukai.text)

        # メッセージ
        elem_info = soup.select_one('#page > table:nth-child(3) > tbody > tr:nth-child(3) > td')
        if elem_info:
            str_info = elem_info.text
            # TODO アンケート部分作成する場合、一時的にコメントアウト
            if '前回行使' in str_info:
                print(str_info)
                return

        # 「会社提案議案について一括して賛成とされる場合」
        elem_btn = ys.elem_selector('#page > form > table:nth-child(4) > tbody > tr > td > table > tbody > tr:nth-child(2) > td > div > a > input')
        ys.click(elem_btn)
        yoshium.wait()

        # 送信
        elem_btn = ys.elem_selector(
            '#page > table:nth-child(4) > tbody > tr > td > table:nth-child(3) > tbody > tr:nth-child(2) > td > div > a > input')
        ys.click(elem_btn)

        # メッセージ
        elem_info = ys.elem_selector('#page > table:nth-child(3) > tbody > tr:nth-child(3) > td')
        if elem_info:
            print(elem_info.text)

        # 議決権行使期間外等
        elem_info = ys.elem_selector('#page > table:nth-child(2) > tbody > tr:nth-child(3) > td > table > tbody > tr > td')
        if elem_info:
            if '議決権行使期間外' in elem_info.text:
                print('- 議決権行使期間外等によりログインができません。')
                return

        # =======================
        # 議決権行使プレゼントがある場合
        # （GIFTPAD）
        # =======================
        elems_check = []
        # 2024年 本田技研
        # elems_check.append(ys.elem_selector(
        #     '#page > table:nth-child(4) > tbody > tr:nth-child(1) > td > table:nth-child(1) > tbody > tr:nth-child(3) > td > font'))
        # 2024年 シュッピン
        elems_check.append(ys.elem_selector(
            '#page > table:nth-child(4) > tbody > tr:nth-child(1) > td > table:nth-child(1) > tbody > tr:nth-child(3) > td > input[type=checkbox]'))

        elem_check = None
        for elem in elems_check:
            if elem:
                elem_check = elem
                break

        if elem_check:
            ys.click(elem_check)
            elem_btn = ys.elem_selector('#item_BUTTON_KOCHIRA0')
            ys.click(elem_btn)

            # 応募フォームへ進む
            # Javasqriptでクリックできない
            # #login_form フォーム全体
            elem_btn = ys.elem_selector('#login_btn > i')
            if elem_btn:
                ys.click(elem_btn)

            # メルアド入力
            ys.write(str_input=MAIL_ADDRESS, into=ys.elem_id('q_num_1'))
            ys.write(str_input=MAIL_ADDRESS, into=ys.elem_id('q_num_1_confirm'))

            # 同意する
            ys.click(ys.elem_selector('#frm_input > dl:nth-child(5) > dd > label > input[type=radio]'))

            # 誕生年
            elem_dropdown = ys.elem_selector('#frm_input > dl:nth-child(6) > dd > select')
            if elem_dropdown:
                ys.elem_dropdown_select(elem=elem_dropdown,str_text=BIRTH_YEAR)

            # # 性別
            # elem_text = ys.elem_text(SEX)
            # if elem_text:
            #     ys.click(elem_text)
            #
            # # 職業
            # elem_text = ys.elem_text(PROFESSION)
            # if elem_text:
            #     ys.click(elem_text)


            input('- 回答を確認したらEnterキーを押してください。')

            # 送信する
            ys.click(ys.elem_id('a_entry'))
            return


        input('- プレゼント企画がないか確認してください。(Press Enter key to next.)')



    # TODO どのシステムか判定する
    # みずほ, 三井住友
    # URLに'/smtphn/service'を含む
    if 'smtphn' in url:
        print('- 議決権行使ページ(smtphn)')
        koushi_smtphn_site()

    elif 'soukai-portal.net' in url:
        print('- 株主総会ポータル')

        # 議決権行使ボタンをクリックする
        elem_btn = ys.elem_id('kb0001100_stockuserUrl')
        if elem_btn:
            ys.click(elem_or_str=elem_btn)
            # ウィンドウの切り替え
            ys.close_window()
            ys.switch_to()
            url = ys.get_driver().current_url
            if 'smtphn' in url:
                print('- 議決権行使ページ(smtphn)')
                koushi_smtphn_site(ys=ys)
        else:
            print('- 議決権行使ボタンが見つかりません。(press Enter key to next.)')

    elif 'e-voting' in url:
        # UFJ
        print('- 議決権行使ページ(e-voting)')
        koushi_evoting_site()

    else:
        # ログインID手動入力
        url = ys.get_driver().current_url
        if url == "https://evote.tr.mufg.jp/" or url == "https://www.web54.net/":
            return False

        print('- ★不明な議決権行使サイト')
        input('- 手動で入力し、完了したらEnterキーを押してください。(press Enter key to next.)')
    return True

if __name__ == '__main__':
    # # imgディレクトリ内の全てのHEICファイルを取得する
    # files = glob.glob('./img/*.HEIC')
    #
    # # PNGに変換
    # for file in files:
    #     conv_to_png(file)

    # TODO jpegファイルの場合はpngに変換する必要がある

    # webブラウジングのためのオブジェクトを生成する
    ys = yoshium.Yoshium()

    # imgディレクトリ内の全てのpngファイルを取得する
    img_directory_path = r'./img/'
    img_file_name = '*.png'
    img_file_path = img_directory_path + img_file_name
    files = glob.glob(img_file_path)
    count = 0
    # 読み取りできなかったもの
    list_not_read = []
    # ログインID手動入力
    list_manual = []
    for f in files:
        count += 1
        print('*********************************')
        list_data = get_data_qrdec(f)
        url = get_url(list_data)
        if url is not None:
            print(str(count) + "枚目("+f+") " + url)
            # webbrowser.open(url, new=0, autoraise=True)
            result = giketuken_koushi(ys, url)
            if not result:
                print("- ログインIDが手動入力となるため処理を行いません。")
                list_manual.append(f)
        else:
            print(str(count) + "枚目(" + f + ") URLを読み取れませんでした。")
            list_not_read.append(f)
        yoshium.wait()
    print()
    print('*********************************')
    print('- 全ての処理が完了しました。')
    if count == 0:
        print('- 画像ファイルがありません。')
        print('  imgフォルダに議決権行使書のQRコード記載面のPNG画像を入れてください。')
        quit()
    elif len(list_not_read) == 0:
        print('- 読み取れなかった行使書はありません。')
    else:
        print('- ' + str(count) + '枚中、' + str(len(list_not_read)) + '枚の読み取りができませんでした。')
        print('※ 読み取りができなかった行使書')
        for f in list_not_read:
            print('・' + f)
    if len(list_manual) == 0:
        print('- 未処理の行使書はありません。')
    else:
        print('- ' + str(len(list_manual)) + '枚はログインID手動入力のため未処理です。')
        print('※ 未処理の行使書')
        for f in list_manual:
            print('・' + f)

    answer = input('- 議決権行使書の画像ファイルを削除しますか？(y or n)')
    if answer == 'y' or answer == 'Y':
        try:
            # ディレクトリごと削除して同名のディレクトリを作成
            shutil.rmtree(img_directory_path)
            os.mkdir(img_directory_path)
            f = open(img_directory_path + '.gitkeep', 'w')
            f.write('')
            f.close()
            print('- ファイルを削除しました。')
        except Exception as e:
            print('- 正常に完了しませんでした。')
            print(e)



