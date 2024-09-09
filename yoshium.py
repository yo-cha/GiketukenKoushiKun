import os
import signal

import requests
import selenium.webdriver.support.select
from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.chrome.service import Service as ChromeService
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time


def wait(num_sec=2):
    """
    指定の秒数停止する
    :param num_sec:int 指定秒数
    :return: 無し
    """
    time.sleep(num_sec)


class Yoshium:
    # webドライバ
    driver = None
    # セッション
    session = None

    def __init__(self, headless=False):
        self.driver = None
        self.session = None

        def start_chrome(headless=False):
            """
            Chromeを起動する
            :param headless:
            :return: 無
            """
            if headless:
                # ヘッドレスモード指定時
                op = webdriver.ChromeOptions()
                op.add_argument("--headless=new")
                # self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=op)
                self.driver = webdriver.Chrome(options=op)
            else:
                # self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
                self.driver = webdriver.Chrome()

            # セッションの取得
            # TODO 必要か？
            self.session = requests.session()

        start_chrome(headless)

    def go_to(self, url):
        """
        指定したURLを開く
        :param url:
        :return:
        """
        self.driver.get(url)

    def get_driver(self):
        """
        ドライバを返す
        :return:
        """
        return self.driver

    def get_session(self):
        """
        セッションを返す
        :return: セッションオブジェクト
        """
        return self.session

    def set_session(self, session):
        """
        セッションを渡す
        :param session:
        :return:
        """
        self.session = session

    def cook_soup(self, response=None, encode='utf-8', parser="html.parser"):
        # TODO パーサーはもっと速いのが使えるかも
        if response is None:
            html = self.driver.page_source.encode(encode)
            soup = BeautifulSoup(html, parser)
        else:
            soup = BeautifulSoup(response.text, parser)
        return soup

    def switch_to(self, title=None, num_window=0):
        """
        指定したタイトル名または番号のウィンドウに切り替える
        :param title:
        :param num_window:
        :return:
        """

        # ウィンドウハンドルを取得する
        win_handle_array = self.driver.window_handles

        # タイトルが入力されていないなら、ウィンドウの番号から切り替える
        # 引数無しの場合、0番目のウィンドウに切り替える
        if title is None:
            self.driver.switch_to.window(win_handle_array[num_window])
            return

        # もし2つ以上のウィンドウがあるなら、タイトル名から切り替え先を探す
        if 1 < len(win_handle_array):
            # 現在のウィンドウ
            now_window = self.driver.current_window_handle

            # 指定した文字列がタイトルに含まれるウィンドウがあったか
            flg = False

            for window in win_handle_array:
                # ウィンドウを切り替える
                self.driver.switch_to.window(window)
                if title in self.driver.title:
                    flg = True
                    break
            if not flg:
                # 全てのウィンドウを調べ、タイトルに文字列が含まれるものがなかった場合は下のウィンドウに戻す
                self.driver.switch_to.window(now_window)

    def close_window(self):
        """
        1つのウィンドウを残し他を閉じる
        :return:
        """
        # ウィンドウハンドルを取得する
        win_handle_array = self.driver.window_handles

        # ウィンドウが複数ある場合
        if 1 < len(win_handle_array):
            # 現在のウィンドウを消す
            self.driver.close()
        # TODO 直前のウィンドウに切り替えはできるか？

    def kill_browser(self):
        """
        ブラウザを閉じる
        :param self:
        :return:
        """
        self.driver.quit()

    def keep_browser_open(self):
        """
        ブラウザを開いたままにする
        :return:
        """
        os.kill(self.driver.service.process.pid, signal.SIGTERM)

    def elem_link(self, str_link, partial=True):
        """
        リンクされている文字列から最初に見つかったリンク要素を1つ探す
        :param str_link: 文字列
        :param partial: Trueなら部分一致、Falseなら完全一致
        :return:
        """
        if partial:
            # 部分一致でリンクテキストを探す
            elems = self.driver.find_elements(By.PARTIAL_LINK_TEXT, str_link)
        else:
            # 完全一致
            elems = self.driver.find_elements(By.LINK_TEXT, str_link)
        if len(elems) > 0:
            # 要素が存在するとき
            return elems[0]
        else:
            # 要素が存在しないとき
            return None

    def elems_link(self, str_link, partial=True):
        """
        リンクされている文字列からリンク要素を配列で返す
        :param str_link:
        :param partial:
        :return:
        """
        if partial:
            # 部分一致でリンクテキストを探す
            elems = self.driver.find_elements(By.PARTIAL_LINK_TEXT, str_link)
        else:
            # 完全一致
            elems = self.driver.find_elements(By.LINK_TEXT, str_link)

        # リンクの取得
        elems = self.driver.find_elements(By.LINK_TEXT, str_link)
        if len(elems) > 0:
            # 要素が存在するとき
            return elems
        else:
            # 要素が存在しないとき
            return None

    def elem_selector(self, str_selector):
        """
        CSSセレクタから最初に見つかった要素を1つ返す
        :param str_selector:
        :return:
        """
        # 要素の取得
        elems = self.driver.find_elements(By.CSS_SELECTOR, str_selector)
        if len(elems) > 0:
            # 要素が存在するとき
            return elems[0]
        else:
            # 要素が存在しないとき
            return None

    def elems_selector(self, str_selector):
        """
        CSSセレクタから見つかった要素を配列で返す
        :param str_selector:
        :return:
        """
        # 要素の取得
        elems = self.driver.find_elements(By.CSS_SELECTOR, str_selector)
        if len(elems) > 0:
            # 要素が存在するとき
            return elems
        else:
            # 要素が存在しないとき
            return None
    def elem_xpath(self, str_xpath):
        """
        CSSセレクタから最初に見つかった要素を1つ返す
        :param str_xpath:
        :return:
        """
        # 要素の取得
        elems = self.driver.find_elements(By.XPATH, str_xpath)
        if len(elems) > 0:
            # 要素が存在するとき
            return elems[0]
        else:
            # 要素が存在しないとき
            return None

    def elems_xpath(self, str_xpath):
        """
        X-PATHから見つかった要素を配列で返す
        :param str_xpath:
        :return:
        """
        # 要素の取得
        elems = self.driver.find_elements(By.XPATH, str_xpath)
        if len(elems) > 0:
            # 要素が存在するとき
            return elems
        else:
            # 要素が存在しないとき
            return None

    def elem_text(self, str_value=None, above=None, to_right_of=None, below=None, to_left_of=None):
        # TODO （未完成）テキストから要素を取得
        """
        指定したテキストの要素を返す。
        テキストは1つのみ指定可。
        :param str_value: このテキストの要素
        :param above: このテキストの上の要素
        :param to_right_of: このテキストの右の要素
        :param below: このテキストの下の要素
        :param to_left_of: このテキストの左の要素
        :return:
        """
        elem = None
        if above:
            # 指定したテキストの上の要素
            # elem = driver.find_element(By.XPATH, f'//*[contains(text(), "{to_left_of}")]/preceding-sibling::*[1]')
            pass
        elif to_right_of:
            # 指定したテキストの右の要素
            elem = self.driver.find_element(By.XPATH, f'//*[contains(text(), "{to_left_of}")]/following-sibling::*[1]')
            # TODO 指定した先にない場合、一つ親の右の要素の子を指定する
        elif below != None:
            # 指定したテキストの下の要素
            # elem = driver.find_element(By.XPATH, f'//*[contains(text(), "{to_left_of}")]/preceding-sibling::*[1]')
            pass
        elif to_left_of != None:
            # 指定したテキストの左の要素
            elem = self.driver.find_element(By.XPATH, f'//*[contains(text(), "{to_left_of}")]/preceding-sibling::*[1]')
            # TODO 指定した先にない場合、一つ親の左の要素の子を指定する
        else:
            # 指定したテキストの要素
            # TODO エラー
            # selenium.common.exceptions.NoSuchElementException:
            # Message: no such element: Unable to locate element: {"method":"xpath","selector":"//*[contains(text(), "女性")]"}
            elem = self.driver.find_element(By.XPATH, f'//*[contains(text(), "{str_value}")]')
        # TODO 見つけられなかったときは？
        return elem

    def elem_button(self, str_value_or_alt=None):
        """
        表示文字列のボタンの要素を取得する
        :param str_value_or_alt: input要素のvalueまたはaltの値
        :return:
        """
        if len(self.driver.find_elements(By.CSS_SELECTOR, f'input[value="{str_value_or_alt}"]')) > 0:
            # 要素が存在するとき
            return self.driver.find_elements(By.CSS_SELECTOR, f'input[value="{str_value_or_alt}"]')[0]
        elif len(self.driver.find_elements(By.CSS_SELECTOR, f'input[alt="{str_value_or_alt}"]')) > 0:
            # 要素が存在するとき
            return self.driver.find_elements(By.CSS_SELECTOR, f'input[alt="{str_value_or_alt}"]')[0]
        else:
            # 要素が存在しないとき
            return None

    def elem_id(self, str_value=None):
        """
        指定するIDの要素を1つ取得する
        :param str_value:
        :return:
        """
        # TODO 存在しない場合に待つ時間が長いような
        if len(self.driver.find_elements(By.CSS_SELECTOR, f'[id="{str_value}"]')) > 0:
            # 要素が存在するとき
            return self.driver.find_elements(By.CSS_SELECTOR, f'[id="{str_value}"]')[0]
        else:
            # 要素が存在しないとき
            return None

    def click(self, elem_or_str):
        """
        指定した要素または文字列をクリックする
        :param elem_or_str:
        :return:
        """
        # TODO クリック可能になってから押す
        if isinstance(elem_or_str, str):
            # リンクの文字列から要素を取得する
            elem_or_str = self.elem_link(elem_or_str)
        # 要素が存在しない場合は終了する
        if elem_or_str is None:
            return
        # 要素が存在する場合はクリックする
        self.driver.execute_script('arguments[0].click();', elem_or_str)

    def write(self, str_input: str = None, into: 'WebElement' = None, after_tab_key=True):
        """
        指定した要素（テキストフィールド）に文字列を書き込む
        :param after_tab_key:
        :param str_input: 指定する文字列
        :param into: 書き込む要素
        :after_tab_key: 書込み後Tabキー押下するか（フォーカスを移すため）
        :return:
        """
        if str_input is None or into is None:
            return
        else:
            # クリックしてフォーカスを移す
            self.click(into)

            # 入力
            into.send_keys(str_input)

            # Tabキー押下でフォーカスを移す
            if after_tab_key:
                into.send_keys(Keys.TAB)

    def elem_checkbox(self, str_value):
        """
        表示文字列からチェックボックス要素を取得する
        :param str_value:
        :return:
        """
        elem = None
        # 要素の取得
        elem = self.elem_text(to_left_of=str_value)
        return elem

    def elem_dropdown_select(self, elem=None, str_text=None, str_value=None, num_select=0):
        """
        ドロップダウンリストを選択する
        :param str_text: ドロップダウンリストに表示されている文字列
        :param elem: ドロップダウンリストである要素
        :param num_select: 選択する要素の番号
        :return:
        """
        # ドロップダウンリストを選択する
        elem = selenium.webdriver.support.select.Select(elem)

        if str_text:
            # 表示されている文字列から選択
            elem.select_by_visible_text(str_text)
        elif str_value:
            # 中身の値
            elem.select_by_value(str_value)
        else:
            # インデックスから選択
            elem.select_by_index(num_select)


