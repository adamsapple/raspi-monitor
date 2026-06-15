# Pi Monitor for Raspberry PI5

このリポジトリは、Raspberry Pi と PiTFT/ST7735 で動作する簡易モニタ表示アプリです。

## 概要
- CPU / メモリ / ディスク / ファン回転数などを画面に表示します
- systemd サービスとして自動起動できます

## 主なファイル
- `7735.py` : メインの表示アプリ
- `makePilFont.py` : PIL フォントファイル (`.pil`) を生成する補助スクリプト
- `install.sh` : systemd サービスの開始/インストール用スクリプト
- `uninstall.sh` : systemd サービスの停止/アンインストール用スクリプト
- `pimonitor.service` : 自動起動用の systemd 設定
- `requirements.txt` : 必要な Python パッケージ

## 必要環境
- Raspberry Pi 5
- PiTFT / ST7735 対応ディスプレイ
- Python 3.10 以降
- `liblgpio` などの GPIO 関連ライブラリ

## セットアップ
1. 依存関係をインストールします
   ```sh
   python -m venv .venv --system-site-packages
   source .venv/bin/activate
   python -m pip install -r requirements.txt
   ```
2. ~~`pimonitor.service`を開き、配備場所のディレクトリ類を編集します。~~  3の工程で自動で更新されます。
   ```plaintext
   WorkingDirectory = /foo/bar/pimonitor/     # この行と
   ExecStart = /foo/bar/pimonitor/.venv/bin/python /foo/bar/pimonitor/7735.py   # この行を修正
   ```
3. サービスをインストールします
   ```sh
   sudo sh install.sh
   ```
4. フォントを変更する場合は、Pilファイルを生成するヘルパーを用意しました。
   ```sh
   python makePilFont.py
   ```
5. `/boot/firmware/config.txt` へGPIO(BackLightのPin)起動時の状態を設定
   ```
   # GPIO Setting
   gpio=0=op,dh
   gpio=18=op,dl
   ```
6. `rpi-eeprom-config`を編集して電源停止時は3.3vの出力を止める
   `sudo rpi-eeprom-config -e`
   ```
   POWER_OFF_ON_HALT=1
   ```

## 実行方法
### 通常実行
```sh
source .venv/bin/activate
python 7735.py
```

### サービスとして起動/停止
```sh
sudo systemctl start pimonitor.service
sudo systemctl stop pimonitor.service
sudo systemctl status pimonitor.service
```

## フォント生成について
`makePilFont.py` は、`fonts/terminus-font-4.49.1.tar.gz` 内の BDF フォントを読み込み、PIL で利用できる `.pil` フォントへ変換します。他にも色々なケースのフォント変換を行う機能をコメントにしてあります。ソース内を確認してみてください。

## 備考
- `install.sh` は systemd サービスの登録と起動を行います
- 画面表示に依存するため、実機での確認を推奨します
