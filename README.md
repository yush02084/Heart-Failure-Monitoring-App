# 心不全見守りWebアプリ

> 離れて暮らす親（心不全退院後）の異変に、子が気づき**電話をかけるきっかけ**を作るためのプロトタイプWebアプリ

![Status](https://img.shields.io/badge/status-MVP%20設計確定-blue)
![Stack](https://img.shields.io/badge/stack-Flask%20%7C%20SQLite%20%7C%20Vanilla%20JS-green)
![Phase](https://img.shields.io/badge/phase-実装着手前-orange)

⚠️ **本アプリはプロトタイプであり、医療判断を行うものではありません。**

---

## 📋 目次

- [1. プロジェクトの目的](#1-プロジェクトの目的why)
- [2. スコープ](#2-スコープ)
- [3. 技術スタック](#3-技術スタック)
- [4. 想定規模](#4-想定規模)
- [5. データベース設計](#5-データベース設計)
- [6. 主要フロー](#6-主要フロー)
- [7. 判定ロジック](#7-判定ロジック)
- [8. UI/UX 原則](#8-uiux-原則)
- [9. セキュリティ要件](#9-セキュリティ要件mvp最低ライン)
- [10. 将来拡張ロードマップ](#10-将来拡張ロードマップ)
- [11. 確度・参考根拠](#11-確度参考根拠)
- [12. 次のアクション](#12-次のアクション)

> **タイムゾーン**: 全レイヤーで `Asia/Tokyo`（JST）固定
> **Status**: 要件定義フェーズ確定版（v2.1, 2026-04-26）

---

## 1. プロジェクトの目的（Why）

- **主顧客**：離れて暮らす子世代（40〜60代）
- **協力者**：心不全で退院した高齢の親
- **目的**：親の異変（体重・息切れ）に子が気づき、**電話をかけるきっかけを作る**

---

## 2. スコープ

### MVPでやること
- 親による日次入力（体重・息切れ）
- 自動アラート判定（🟢通常／🟡注意／🔴警戒／⚪入力途絶）
- 子による閲覧・既読管理
- 警戒・注意時のメール通知
- 招待リンクによる子の登録
- **子画面から親への電話発信ボタン**（tel:リンク）

### MVPでやらないこと（明示）
- バイタル追加（血圧／SpO2／脈拍）
- 症状チェック（浮腫／夜間呼吸困難／ADL）
- 服薬記録
- LINE通知／Push通知（**スキーマだけ拡張余地を残す**）
- アプリ化（PWA含む）
- 医師アカウント／診療記録連携
- 変更履歴の完全保持（updated_at のみ）
- base_weight 履歴管理（更新日のみ記録）

### 設計上は将来対応する
- M:N の親子関係（兄弟分担／父母両方見守り）
- 通知チャネル切替え（メール → LINE → Push）
- バイタル・症状・服薬の別テーブル拡張
- PostgreSQL 移行（中規模到達時）
- base_weight 履歴テーブル化(フェーズ2)

---

## 3. 技術スタック

| レイヤー | 採用 | 備考 |
|---|---|---|
| Backend | Python / Flask / SQLAlchemy | |
| Database | SQLite3 | 中規模到達時に PostgreSQL へ移行検討 |
| Frontend | HTML / Vanilla CSS / Vanilla JS | フレームワーク禁止 |
| Chart | Chart.js (CDN) | |
| Auth | Flask セッション + bcrypt（**cost factor 12以上**） | OWASP Authentication Cheat Sheet 準拠 |
| Mail | smtplib or Flask-Mail | MVP 段階は同期送信、将来キュー化 |
| Migration | Alembic | 初期マイグレーションでインデックスも投入 |

### 禁止事項
- React / Vue.js / TailwindCSS 等のモダンフレームワーク
- 複雑な認証（OAuth／SSO／多要素）
- 多機能化全般

---

## 4. 想定規模

| フェーズ | 家族数 | DB | 備考 |
|---|---|---|---|
| MVP | 〜10 | SQLite | 自分の親・親族で検証 |
| 小規模運用 | 〜100 | SQLite | クリニック開業後の患者向け配布 |
| 中規模 | 〜1,000 | PostgreSQL | SaaS 化／他院展開時に移行 |

> **設計方針**：MVP段階のスキーマでも中規模まで構造変更不要にする。

---

## 5. データベース設計

### 5.1 テーブル一覧

| テーブル | 役割 | MVP実装 |
|---|---|---|
| `Users` | 親・子の共通ユーザー | ✅ |
| `Watch_Relationships` | 親⇔子の見守り関係（M:N対応） | ✅ |
| `Invitations` | 招待リンク管理（sharing_token） | ✅ |
| `Daily_Records` | 親の日次入力 | ✅ |
| `Record_Read_Status` | 子ごとの既読管理 | ✅ |
| `Notification_Log` | 通知送信履歴(チャネル抽象化) | ✅ |
| `Notification_Preferences` | 子の通知設定 | ✅ |

### 5.2 スキーマ詳細

#### Users
```python
id                       INTEGER PRIMARY KEY
login_id                 TEXT UNIQUE NOT NULL
pin_hash                 TEXT NOT NULL              # bcrypt cost≥12
role                     TEXT NOT NULL              # 'parent' or 'watcher'
name                     TEXT NOT NULL              # 表示名
email                    TEXT                       # 子は必須、親は任意
phone_number             TEXT                       # E.164形式（例: +819012345678）
base_weight              REAL                       # 親のみ使用（基準体重kg）
base_weight_updated_at   DATETIME                   # 親のみ、dry weight 更新日
failed_attempts          INTEGER NOT NULL DEFAULT 0
locked_until             DATETIME                   # ロックアウト解除時刻
created_at               DATETIME NOT NULL
updated_at               DATETIME NOT NULL
deleted_at               DATETIME                   # 論理削除
```

#### Watch_Relationships
```python
id              INTEGER PRIMARY KEY
parent_user_id  INTEGER NOT NULL FK→Users.id
watcher_user_id INTEGER NOT NULL FK→Users.id
status          TEXT NOT NULL              # 'pending' / 'active' / 'revoked'
invited_at      DATETIME NOT NULL
accepted_at     DATETIME
created_at      DATETIME NOT NULL
updated_at      DATETIME NOT NULL
UNIQUE(parent_user_id, watcher_user_id)
```

#### Invitations
```python
id              INTEGER PRIMARY KEY
parent_user_id  INTEGER NOT NULL FK→Users.id
sharing_token   TEXT UNIQUE NOT NULL       # secrets.token_urlsafe(32)
expires_at      DATETIME NOT NULL          # デフォルト 7日後
used_at         DATETIME                   # 使用後にセット
created_at      DATETIME NOT NULL
```

#### Daily_Records
```python
id                    INTEGER PRIMARY KEY
parent_user_id        INTEGER NOT NULL FK→Users.id
record_date           DATE NOT NULL              # JST基準
weight                REAL NOT NULL
breath_condition      INTEGER NOT NULL           # 1=普通 2=ちょっと 3=けっこう 4=とても
alert_level           INTEGER NOT NULL           # 0=⚪ 1=🟢 2=🟡 3=🔴
alert_logic_version   INTEGER NOT NULL           # 判定ロジックのバージョン
created_at            DATETIME NOT NULL
updated_at            DATETIME NOT NULL
deleted_at            DATETIME                   # 論理削除
UNIQUE(parent_user_id, record_date)              # 同一日UPSERT制約
```

#### Record_Read_Status
```python
record_id         INTEGER NOT NULL FK→Daily_Records.id
watcher_user_id   INTEGER NOT NULL FK→Users.id
read_at           DATETIME NOT NULL
PRIMARY KEY(record_id, watcher_user_id)
```

#### Notification_Log
```python
id                INTEGER PRIMARY KEY
watcher_user_id   INTEGER NOT NULL FK→Users.id
record_id         INTEGER NOT NULL FK→Daily_Records.id
channel           TEXT NOT NULL              # 'email' / 将来 'line' / 'push'
sent_at           DATETIME NOT NULL
status            TEXT NOT NULL              # 'sent' / 'failed' / 'bounced'
error_message     TEXT
```

#### Notification_Preferences
```python
watcher_user_id     INTEGER PRIMARY KEY FK→Users.id
email_enabled       BOOLEAN NOT NULL DEFAULT TRUE
line_token          TEXT                       # 将来用、MVPはNULL
push_subscription   TEXT                       # 将来用、MVPはNULL
created_at          DATETIME NOT NULL
updated_at          DATETIME NOT NULL
```

### 5.3 インデックス定義（必須）

Alembic 初期マイグレーションで以下を投入する：

```sql
-- 親の入力履歴取得（最頻クエリ）
CREATE INDEX idx_records_parent_date
  ON Daily_Records(parent_user_id, record_date DESC);

-- 子の見守り対象一覧取得
CREATE INDEX idx_watch_parent_status
  ON Watch_Relationships(parent_user_id, status);

CREATE INDEX idx_watch_watcher_status
  ON Watch_Relationships(watcher_user_id, status);

-- 通知の冪等性確保（同一alertの重複送信防止）
CREATE UNIQUE INDEX idx_notif_unique
  ON Notification_Log(record_id, watcher_user_id, channel);

-- 既読状態の高速取得
CREATE INDEX idx_read_watcher
  ON Record_Read_Status(watcher_user_id, read_at DESC);
```

### 5.4 設計原則

1. **全テーブルに `created_at` / `updated_at`**（SQLAlchemy Mixin で共通化）
2. **論理削除**：`deleted_at` カラムで対応、ハード削除なし
   - 例外：`Invitations` は使用済み・期限切れを日次バッチで物理削除可
3. **UPSERT**：`Daily_Records (parent_user_id, record_date)` の UNIQUE 制約で実現
4. **拡張用テーブル分離原則**：`Daily_Records` にバイタル系カラムを追加しない。`Vitals` / `Symptoms` / `Medications_Log` を別テーブルで `parent_user_id + record_date` 結合
5. **通知の抽象化**：`Notification_Log.channel` で全チャネル受け止め
6. **MVP段階のUI制約**：1親=1子招待のみに制限（スキーマはM:Nのまま温存）
7. **タイムゾーン**：DB保存・アプリロジック・表示すべて `Asia/Tokyo` 固定。`record_date` も JST の暦日
8. **PINハッシュ**：bcrypt cost factor 12 以上、生PINは絶対に保存・ログ出力しない
9. **判定ロジックのバージョニング**：閾値変更時は `alert_logic_version` をインクリメント、過去データの再計算は行わない

---

## 6. 主要フロー

### 6.1 親の登録・日次入力フロー
1. 親が login_id + 4桁PIN で登録 → `Users(role='parent')` 作成
2. base_weight + base_weight_updated_at を初期設定
3. 毎日：体重 + 息切れ4択を入力 → `Daily_Records` UPSERT
4. UPSERT時に `alert_level` と `alert_logic_version` を自動算出して保存
5. `alert_level >= 2` の場合、紐付く active な watcher 全員に通知（既送信は重複しない）

### 6.2 子の招待・登録フロー
1. 親が「招待リンク発行」 → `Invitations` レコード作成、URL生成
2. 親が口頭/LINE/メール等で URL を子に共有
3. 子がリンクを開く → サーバ側で以下を確認：
   - `used_at IS NULL`
   - `expires_at > 現在時刻（JST）`
   - 満たさない場合は明示的にエラー画面（再発行を促す）
4. 子がアカウント登録（メール + パスワード + 電話番号任意）
5. 登録完了時、**同一トランザクション内で**：
   - `Users(role='watcher')` 作成
   - `Notification_Preferences(email_enabled=TRUE)` 作成（**必ず作る**）
   - `Watch_Relationships` を `status='active'` で作成
   - `Invitations.used_at` をセット（再利用不可化）
6. 以降は子は通常ログインで閲覧

### 6.3 通知フロー
1. 親の入力で `alert_level >= 2` のレコードが生成される
2. `Watch_Relationships(status='active')` の全 watcher を取得
3. 各 watcher の `Notification_Preferences.email_enabled` を確認
4. メール送信を試行 → `Notification_Log` に結果記録
5. 同一 (record_id, watcher_user_id, channel) の組み合わせは UNIQUE 制約で重複送信不可
6. 子がアプリで該当レコードを開いた時点で `Record_Read_Status` 作成

### 6.4 ログイン保護フロー
1. login_id + PIN 入力
2. `Users.locked_until > 現在時刻` の場合は即拒否（残り時間を表示）
3. PIN照合：
   - 成功 → `failed_attempts = 0` にリセット、ログイン成功
   - 失敗 → `failed_attempts += 1`
4. ロックアウト判定：
   - 累計 5 回失敗 → `locked_until = 現在 + 15分`
   - 累計 30 回失敗 → `locked_until = 現在 + 24時間`
5. ロック解除後は `failed_attempts` を 0 に戻す

---

## 7. 判定ロジック

### 7.1 基準体重との差分計算
- **1〜3日目**：`weight - base_weight`
- **4日目以降**：`weight - 比較対象weight`
  - 比較対象は **3日前のレコード**を第一候補
  - 3日前データが欠損 → **過去7日以内の直近の有効レコード**で代用
  - 過去7日以内に有効レコードなし → `base_weight` にフォールバック

### 7.2 アラート判定（OR条件）

| Level | 条件 | 表示 |
|---|---|---|
| 3 (🔴 警戒) | 息切れ「とても/けっこう苦しい」 OR 体重差 +2.0kg 以上 | 赤バッジ + 通知 |
| 2 (🟡 注意) | 息切れ「ちょっと苦しい」 OR 体重差 +1.5〜+1.9kg | 黄バッジ + 通知 |
| 1 (🟢 通常) | 上記以外で正常入力 | 緑バッジのみ |
| 0 (⚪ 入力途絶) | 14日以上未入力 | 子側に「入力途絶」通知（注意レベル相当の扱い） |

### 7.3 注意事項
- 体重差は**増加方向のみ**評価（減量は alert_level に影響しない）
- 同日複数回入力時は最新値で再判定（UPSERT）
- 判定時に `alert_logic_version` を保存。閾値変更時は version をインクリメント、過去データは再計算しない
- `alert_level=0` の判定はアプリ層の日次バッチで実行（子画面表示時に動的計算でも可）

### 7.4 base_weight の運用
- MVP では親のプロフィール画面から手動更新可、`base_weight_updated_at` を必ず更新
- 退院時の dry weight は主治医診察ごとに見直すのが標準
- 「最終更新から90日経過」を画面に表示し、再評価を促す

---

## 8. UI/UX 原則

### 高齢者（親）画面
- 文字サイズ最低 18px、ボタン最低 60×60px
- 1画面1機能、画面遷移最小化
- 入力は数値テンキー + ラジオボタン4択のみ
- 完了画面で大きな緑チェック表示

### 子画面
- 一覧表示でアラート色を即視認できる
- グラフ期間切替（7日／30日／90日／1年／全期間）
- 未読バッジは個別管理（兄弟で既読が混ざらない）
- **警戒・注意バナーに「📞 親に電話する」ボタン**（`tel:phone_number` リンク）
- 入力途絶（alert_level=0）も同様に電話ボタン表示

---

## 9. セキュリティ要件（MVP最低ライン）

| 項目 | 内容 | 確度・根拠 |
|---|---|---|
| パスワード保管 | bcrypt cost≥12、生値保存禁止 | 高（OWASP） |
| ロックアウト | 5回/15分、30回/24時間 | 中（一般的慣行） |
| セッション | Flask の `SESSION_COOKIE_SECURE=True`、`HTTPONLY=True`、`SAMESITE='Lax'` | 高（OWASP） |
| HTTPS | 本番環境必須（Let's Encrypt） | 高 |
| sharing_token | `secrets.token_urlsafe(32)`、推測不可長 | 高（CSPRNG） |
| トークン期限 | デフォルト7日、使用済みは即失効 | 中（実運用判断） |
| 入力検証 | weight: 20〜250kg、breath: 1〜4 のみ受理 | 高 |
| ログ | PIN・パスワード・トークンは絶対にログ出力しない | 高 |

---

## 10. 将来拡張ロードマップ

### フェーズ2（〜100家族、MVP運用安定後）

| 機能 | スキーマ変更 | 推定工数 |
|---|---|---|
| 入力リマインダー | `Notification_Log.trigger_type` 列追加 | 2〜3日 |
| 主たる見守り手 | `Watch_Relationships.is_primary BOOLEAN` | 0.5日 |
| 異常値検知（前日比±5kg） | アプリ層のみ | 1日 |
| base_weight 履歴 | `Base_Weight_History` 新設 | 2日 |
| バックアップ運用 | `.backup` 日次cron + 7世代保持 | 1日 |

### フェーズ3（〜500家族、クリニック患者展開）

| 機能 | スキーマ変更 | 推定工数 |
|---|---|---|
| バイタル拡張 | `Vitals`（BP/SpO2/HR）新設 | 5日 |
| 症状チェック | `Symptoms`（浮腫/夜間呼吸困難/ADL）新設 | 5日 |
| 服薬記録 | `Medications_Log` 新設 | 7日 |
| LINE通知 | 既存スキーマ流用、API実装のみ | 5日 |
| 監査ログ | `Audit_Log(actor_id, action, target, ts)` | 3日 |
| 入力訂正履歴 | `Daily_Records_History` 新設 | 3日 |

### フェーズ4（〜1000家族、SaaS化／他院展開）

| 機能 | 移行対象 | 推定工数 |
|---|---|---|
| PostgreSQL 移行 | 全テーブル | 7〜10日 |
| 医師/看護師ロール | `Users.role` 拡張＋専用テーブル | 14日 |
| 5年保存ポリシー | アーカイブテーブル＋月次バッチ | 7日 |
| Web Push（PWA化） | フロントエンド大改修 | 14〜21日 |
| PDFサマリ出力 | WeasyPrint導入 | 5日 |
| マルチテナント化 | `tenants` テーブル＋全FK拡張 | 14日 |

---

## 11. 確度・参考根拠

- 心不全の在宅モニタリング項目（体重・呼吸困難）：日本循環器学会／日本心不全学会 急性・慢性心不全診療ガイドライン（2017年改訂版、2021年フォーカスアップデート）。確度：高
- dry weight の主治医診察ごとの見直し：同上ガイドライン。確度：高
- 季節性増悪の臨床的意義：Mosterd & Hoes, Heart 2007;93:1137-1146。確度：高
- SQLite のスケール特性：公式 [Appropriate Uses For SQLite](https://www.sqlite.org/whentouse.html)。確度：高
- パスワード保管／ロックアウト：[OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)。確度：高
- 医療記録保存義務（5年）：医師法施行規則第23条。**本アプリは医療記録には該当しない**ため法的義務外。確度：高
- ロックアウト具体閾値（5回/15分等）：一般的慣行に基づく実装判断、明確な医学的根拠なし。確度：中

---

## 📜 ライセンス

未定（個人プロジェクト）

## 🦜 作者

[@yu_sh02084](https://x.com/yu_sh02084) — 循環器内科医 × MSC × SUNABACO programming school

---

*Last updated: 2026-04-26 (v2.1)*
