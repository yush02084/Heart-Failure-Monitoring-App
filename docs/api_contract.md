# API契約・テンプレート仕様 v1

> **目的**：3人体制（A=サーバー、B=親画面、C=子画面）が並行作業するための事前決定事項
> **使い方**：A は実装ガイド、B/C はテンプレート作成時のリファレンス
> **Day 1 朝の sync**：このドキュメントを30分で読み合わせ、不明点だけ質問
> **変更ルール**：実装中の変更は Slack/LINE で即共有 + このドキュメントを更新

---

## 1. ルート一覧

| メソッド | URL | 担当 | 用途 |
|---|---|---|---|
| GET | `/` | A | ルート（認証状態でリダイレクト） |
| GET | `/auth/register/parent` | A→B | 親登録画面表示 |
| POST | `/auth/register/parent` | A | 親登録処理 |
| GET | `/auth/login` | A→B,C | ログイン画面表示 |
| POST | `/auth/login` | A | ログイン処理 |
| POST | `/auth/logout` | A | ログアウト |
| GET | `/auth/register/watcher/<token>` | A→C | 子登録画面表示（招待リンク経由） |
| POST | `/auth/register/watcher/<token>` | A | 子登録処理 |
| GET | `/parent/home` | A→B | 親ホーム画面 |
| GET | `/parent/input` | A→B | 日次入力画面 |
| POST | `/parent/input` | A | 日次入力処理 |
| GET | `/parent/invitations` | A→B | 招待リンク発行画面 |
| POST | `/parent/invitations` | A | 招待リンク発行処理 |
| GET | `/watcher/dashboard` | A→C | 子ダッシュボード |
| GET | `/watcher/parent/<int:parent_id>` | A→C | 親詳細画面 |

---

## 2. 各ルート詳細

### 2.1 GET `/`（ランディング）
- **担当**：A
- **処理**：
  - 未ログイン → `/auth/login` にリダイレクト
  - 親としてログイン中 → `/parent/home` にリダイレクト
  - 子としてログイン中 → `/watcher/dashboard` にリダイレクト
- **テンプレート**：なし（リダイレクトのみ）

---

### 2.2 GET `/auth/register/parent`（親登録画面）
- **担当**：A → B
- **テンプレート**：`templates/auth/register_parent.html`
- **context**：
  ```python
  {
      "form": RegisterParentForm()  # WTForms オブジェクト
  }
  ```
- **B が書くべきHTML（要素のname属性）**：
  | name | type | 必須 | 制約 |
  |---|---|---|---|
  | `login_id` | text | ✅ | 4-20字、半角英数 |
  | `pin` | password | ✅ | 4桁数字 |
  | `pin_confirm` | password | ✅ | pin と一致 |
  | `name` | text | ✅ | 1-20字 |
  | `phone_number` | tel | 任意 | E.164形式 |
  | `base_weight` | number | ✅ | 20.0〜250.0、step=0.1 |
  | `csrf_token` | hidden | ✅ | `{{ form.csrf_token }}` |

- **送信先**：同URL に POST

---

### 2.3 POST `/auth/register/parent`（親登録処理）
- **担当**：A
- **処理**：
  1. CSRF 検証
  2. バリデーション失敗 → 同画面を errors 付きで再描画
  3. login_id 重複 → エラー flash + 再描画
  4. Users(role='parent') 作成、PIN は bcrypt でハッシュ
  5. base_weight + base_weight_updated_at 設定
  6. セッション作成
  7. `/parent/home` にリダイレクト + flash success
- **flash メッセージ**：
  - 成功：`「登録が完了しました。今日の体重を入力してください。」`
  - 失敗：エラー内容（フィールドエラーは form.errors に格納）

---

### 2.4 GET `/auth/login`（ログイン画面）
- **担当**：A → B/C 共有（B が主担当）
- **テンプレート**：`templates/auth/login.html`
- **context**：
  ```python
  {
      "form": LoginForm()
  }
  ```
- **HTML 要素**：
  | name | type | 必須 |
  |---|---|---|
  | `login_id` | text | ✅ |
  | `pin` | password | ✅ |
  | `csrf_token` | hidden | ✅ |

---

### 2.5 POST `/auth/login`（ログイン処理）
- **担当**：A
- **処理**：
  1. login_id で Users を検索（deleted_at IS NULL）
  2. PIN bcrypt 照合
  3. 失敗 → flash error + 再描画
  4. 成功 → セッション作成 → role に応じて `/parent/home` または `/watcher/dashboard` へリダイレクト
- **flash**：
  - 失敗：`「ログインIDまたはPINが間違っています。」`

---

### 2.6 POST `/auth/logout`
- **担当**：A
- **処理**：セッション破棄 → `/auth/login` リダイレクト
- **flash**：`「ログアウトしました。」`

---

### 2.7 GET `/auth/register/watcher/<token>`（子登録画面）
- **担当**：A → C
- **テンプレート**：`templates/auth/register_watcher.html`
- **context**：
  ```python
  {
      "form": RegisterWatcherForm(),
      "parent_name": "山田太郎",  # 招待元の親の名前
      "token": "xxxxx",  # フォームの hidden に入れる
  }
  ```
- **エラーハンドリング**（A 側）：
  - トークン不正 → 「招待リンクが無効です」エラー画面
  - トークン期限切れ → 「招待リンクの有効期限が切れています」エラー画面
  - トークン使用済み → 「この招待リンクは既に使用されています」エラー画面
- **HTML 要素**：
  | name | type | 必須 | 制約 |
  |---|---|---|---|
  | `login_id` | text | ✅ | 4-20字 |
  | `password` | password | ✅ | 8文字以上 |
  | `password_confirm` | password | ✅ | password と一致 |
  | `name` | text | ✅ | |
  | `email` | email | ✅ | RFC形式 |
  | `phone_number` | tel | 任意 | |
  | `token` | hidden | ✅ | URLから取得 |
  | `csrf_token` | hidden | ✅ | |

---

### 2.8 POST `/auth/register/watcher/<token>`（子登録処理）
- **担当**：A
- **処理**（**同一トランザクション**）：
  1. トークン検証
  2. Users(role='watcher') 作成、password ハッシュ
  3. Notification_Preferences(email_enabled=TRUE) 作成
  4. Watch_Relationships(status='active') 作成
  5. Invitations.used_at セット
  6. セッション作成 → `/watcher/dashboard` リダイレクト
- **flash**：成功時 `「登録完了！山田太郎さんの記録を見守れるようになりました。」`

---

### 2.9 GET `/parent/home`（親ホーム）
- **担当**：A → B
- **要件**：parent としてログイン必須（@login_required_parent）
- **テンプレート**：`templates/parent/home.html`
- **context**：
  ```python
  {
      "user": user_dict,           # 下記参照
      "today_record": record_dict_or_None,  # 今日の入力。未入力ならNone
      "recent_records": [record_dict, ...], # 過去7日（古い順）
      "needs_input_today": True/False,      # 今日まだ入力していないか
  }
  ```
- **B が画面に表示する内容**：
  - ユーザー名表示（`{{ user.name }}さん、こんにちは`）
  - 今日の入力ボタン（needs_input_today=True なら大きく表示）
  - 今日の記録表示（today_record があれば）
  - 過去7日の表（アラート色分け）
  - 招待リンク発行画面へのリンク（`/parent/invitations`）
  - ログアウトボタン

---

### 2.10 GET `/parent/input`（日次入力画面）
- **担当**：A → B
- **要件**：parent ログイン必須
- **テンプレート**：`templates/parent/input.html`
- **context**：
  ```python
  {
      "form": DailyRecordForm(),
      "today_record": record_dict_or_None,  # 既に入力済みなら値を表示
      "today_str": "2026年04月27日(月)",    # 表示用日付
  }
  ```
- **HTML 要素**：
  | name | type | 必須 | 制約 |
  |---|---|---|---|
  | `weight` | number | ✅ | 20.0〜250.0、step=0.1 |
  | `breath_condition` | radio | ✅ | 1, 2, 3, 4 |
  | `csrf_token` | hidden | ✅ | |

- **B が書く HTML 構造**：
  ```html
  <input type="number" name="weight" step="0.1" inputmode="decimal" required>

  <input type="radio" name="breath_condition" value="1" id="breath-1">
  <label for="breath-1">普通</label>

  <input type="radio" name="breath_condition" value="2" id="breath-2">
  <label for="breath-2">ちょっと苦しい</label>

  <input type="radio" name="breath_condition" value="3" id="breath-3">
  <label for="breath-3">けっこう苦しい</label>

  <input type="radio" name="breath_condition" value="4" id="breath-4">
  <label for="breath-4">とても苦しい</label>
  ```

---

### 2.11 POST `/parent/input`（日次入力処理）
- **担当**：A
- **処理**：
  1. バリデーション
  2. 判定ロジック実行 → alert_level 算出
  3. Daily_Records UPSERT（同日入力は上書き）
  4. `/parent/home` リダイレクト + flash
- **flash**：
  - alert_level=1 → `「今日の記録を保存しました。順調です 🟢」`
  - alert_level=2 → `「今日の記録を保存しました。少し注意してください 🟡」`
  - alert_level=3 → `「今日の記録を保存しました。お子さんに連絡しましょう 🔴」`

---

### 2.12 GET `/parent/invitations`（招待リンク発行画面）
- **担当**：A → B
- **テンプレート**：`templates/parent/invitations.html`
- **context**：
  ```python
  {
      "active_invitations": [
          {
              "id": 1,
              "url": "http://localhost:5000/auth/register/watcher/abc123",
              "expires_at_str": "2026年05月04日まで",
              "created_at_str": "2026年04月27日 18:30",
          },
          ...
      ],
      "form": InvitationCreateForm(),  # csrf_tokenのみ
  }
  ```
- **B が書く要素**：
  - 「新しい招待リンクを発行」ボタン（POSTフォーム）
  - 既存の招待リンク一覧（コピーボタン付き）

---

### 2.13 POST `/parent/invitations`（招待発行処理）
- **担当**：A
- **処理**：
  1. sharing_token 生成（`secrets.token_urlsafe(32)`）
  2. expires_at = now + 7days
  3. Invitations 作成
  4. `/parent/invitations` リダイレクト + flash
- **flash**：`「招待リンクを発行しました。お子さんにこのURLを送ってください。」`

---

### 2.14 GET `/watcher/dashboard`（子ダッシュボード）
- **担当**：A → C
- **要件**：watcher ログイン必須
- **テンプレート**：`templates/watcher/dashboard.html`
- **context**：
  ```python
  {
      "user": user_dict,
      "watched_parents": [
          {
              "parent_id": 1,
              "parent_name": "山田太郎",
              "phone_number": "+819012345678",
              "latest_record": record_dict_or_None,
              "alert_level": 1,             # 0/1/2/3
              "alert_emoji": "🟢",
              "alert_color_class": "alert-1",
              "alert_label": "通常",
              "last_input_date_str": "2026年04月27日",
              "days_since_last_input": 0,   # 0=今日入力済
          },
          ...
      ]
  }
  ```
- **C が書く要素**：
  - 親ごとのカード表示（アラート色分け）
  - 警戒・注意の親があれば上に並べる
  - 各親カードから詳細（`/watcher/parent/<id>`）へのリンク

---

### 2.15 GET `/watcher/parent/<int:parent_id>`（親詳細画面）
- **担当**：A → C
- **要件**：watcher ログイン + Watch_Relationships で active な紐付けがあること
- **テンプレート**：`templates/watcher/parent_detail.html`
- **context**：
  ```python
  {
      "parent": {
          "id": 1,
          "name": "山田太郎",
          "phone_number": "+819012345678",
          "tel_link": "tel:+819012345678",  # そのまま href に使える
      },
      "today_alert": {
          "level": 3,
          "emoji": "🔴",
          "color_class": "alert-3",
          "label": "警戒",
          "should_show_call_button": True,  # level >= 2 で True
      },
      "recent_records": [record_dict, ...],  # 過去7日（新しい順）
  }
  ```
- **C が書く要素**：
  - 親名と電話ボタン（`should_show_call_button=True` なら表示）
  - 今日のアラート（大きく色分け）
  - 過去7日テーブル
  - 「親一覧に戻る」リンク

---

## 3. テンプレート context の共通データ形状

### 3.1 `user_dict`（共通）
```python
{
    "id": 1,
    "name": "山田太郎",
    "role": "parent",  # または "watcher"
}
```

### 3.2 `record_dict`（Daily_Records 表示用）
```python
{
    "date_str": "2026年04月27日(月)",  # 表示用
    "date_iso": "2026-04-27",          # data-attribute用
    "weight": 62.5,
    "weight_diff": "+0.3",             # base_weight差 or 3日前差、文字列
    "breath_condition": 1,             # 数値（1-4）
    "breath_label": "普通",            # 表示用ラベル
    "alert_level": 1,                  # 0-3
    "alert_emoji": "🟢",
    "alert_color_class": "alert-1",    # CSSクラス
    "alert_label": "通常",
}
```

### 3.3 breath_condition の対応表（重要）
| 値 | breath_label | 意味 | 判定への影響 |
|---|---|---|---|
| 1 | 普通 | 苦しくない | alert_level=1 (条件なし) |
| 2 | ちょっと苦しい | 軽度 | alert_level=2 |
| 3 | けっこう苦しい | 中等度 | alert_level=3 |
| 4 | とても苦しい | 重度 | alert_level=3 |

### 3.4 alert_level の対応表（重要）
| level | emoji | label | color_class | 通知 | 電話ボタン |
|---|---|---|---|---|---|
| 0 | ⚪ | 入力途絶 | alert-0 | あり（フェーズ2） | 表示 |
| 1 | 🟢 | 通常 | alert-1 | なし | 非表示 |
| 2 | 🟡 | 注意 | alert-2 | あり（フェーズ2） | 表示 |
| 3 | 🔴 | 警戒 | alert-3 | あり（フェーズ2） | 表示 |

---

## 4. CSS クラス命名規則

### 4.1 アラート色分け
```css
.alert-0 { background-color: #e0e0e0; color: #555; }  /* グレー */
.alert-1 { background-color: #d4edda; color: #155724; } /* 緑 */
.alert-2 { background-color: #fff3cd; color: #856404; } /* 黄 */
.alert-3 { background-color: #f8d7da; color: #721c24; } /* 赤 */
```
↑ A が `static/css/base.css` に定義する。B/C はクラスを使うだけ。

### 4.2 共通コンポーネント
| クラス | 用途 |
|---|---|
| `.flash` | flash メッセージ共通 |
| `.flash-success` | 成功（緑系） |
| `.flash-error` | 失敗（赤系） |
| `.flash-info` | 情報（青系） |
| `.btn-primary` | メインボタン |
| `.btn-large` | 大きいボタン（親画面用） |
| `.btn-call` | 📞電話ボタン（強調赤） |

---

## 5. Flash メッセージ表示

### 5.1 base.html での実装（A が書く）
```html
{% with messages = get_flashed_messages(with_categories=true) %}
    {% for category, msg in messages %}
        <div class="flash flash-{{ category }}">{{ msg }}</div>
    {% endfor %}
{% endwith %}
```
↑ B/C は触らなくて良い。

### 5.2 カテゴリ規約
- `success`：成功（緑）
- `error`：失敗（赤）
- `info`：情報（青）

---

## 6. url_for() 早見表（B/C 用）

テンプレートでリンクを書くとき：

| やりたいこと | 書き方 |
|---|---|
| ホームへ | `{{ url_for('parent.home') }}` |
| 入力画面へ | `{{ url_for('parent.input') }}` |
| 招待発行画面へ | `{{ url_for('parent.invitations') }}` |
| ログイン画面へ | `{{ url_for('auth.login') }}` |
| ログアウト | `{{ url_for('auth.logout') }}` |
| 子ダッシュボード | `{{ url_for('watcher.dashboard') }}` |
| 親詳細（IDが1の例） | `{{ url_for('watcher.parent_detail', parent_id=parent.id) }}` |
| CSS ファイル | `{{ url_for('static', filename='css/parent.css') }}` |
| JS ファイル | `{{ url_for('static', filename='js/parent_input.js') }}` |

---

## 7. エラーケースの統一扱い

| 状況 | A の処理 | 表示 |
|---|---|---|
| 未ログインで認証必須ページ | `/auth/login` へリダイレクト | flash info `「ログインが必要です」` |
| 権限違い（親が子画面など） | `/` へリダイレクト | flash error `「アクセス権限がありません」` |
| バリデーションエラー | 同画面を再描画 | フォーム上にエラー表示 |
| 招待トークン無効 | エラー画面表示 | エラー専用テンプレート |
| 404 | errors/404.html | B または C が作成 |
| 500 | errors/500.html | B または C が作成 |

### 7.1 フォームエラー表示（B/C 用）
```html
<input type="text" name="login_id" value="{{ form.login_id.data or '' }}">
{% if form.login_id.errors %}
    <span class="field-error">
        {% for error in form.login_id.errors %}{{ error }}{% endfor %}
    </span>
{% endif %}
```

---

## 8. レスポンシブ対応の最低ライン

### 8.1 親画面（B 担当）
- 文字サイズ：`font-size: 18px` 以上（body デフォルト）
- ボタン：`min-width: 60px; min-height: 60px; font-size: 20px;`
- viewport meta：A が base.html に設定済み
- 画面遷移は最小（1画面1機能）

### 8.2 子画面（C 担当）
- スマホ（375px幅）で崩れないこと
- アラート色がパッと見分けられる
- 📞電話ボタンは大きく目立たせる

---

## 9. 動作確認チェックリスト

### Day 3 終了時に動くべきこと
- [ ] 親が登録 → ログイン → ホーム到達
- [ ] 親が体重と息切れを入力 → 保存される
- [ ] 入力に応じて alert_level が計算される
- [ ] 親がホームで過去7日と今日の状態を見られる
- [ ] 親が招待リンクを発行できる
- [ ] 子が招待リンクから登録 → ログイン → ダッシュボード到達
- [ ] 子のダッシュボードに親が表示される
- [ ] 子が親詳細を見られる
- [ ] 警戒・注意時に 📞電話ボタンが表示される
- [ ] tel: リンクが正しい電話番号を持つ

---

## 10. このドキュメントの管理ルール

- バージョン：v1（2026-04-26 作成）
- 更新時：誰でも PR で更新可、merge 後 Slack/LINE で全員に通知
- 不明点：実装中に出たら Slack/LINE で質問 → 回答が決まったらこのドキュメントに追記
- 衝突時：A の判断を優先（実装影響が最も大きいため）

---

*Last updated: 2026-04-26*
*Day 1 朝の sync で全員で読み合わせ*
