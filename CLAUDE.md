# CLAUDE.md — 心不全見守りWebアプリ

このファイルをClaudeが読んでいる場合、以下のルールと設定に従うこと。

---

## プロジェクト概要

- **目的**: 離れて暮らす親（心不全退院後）の異変に、子が気づいて電話するきっかけを作るプロトタイプ
- **スタック**: Flask / SQLite / Vanilla JS / Jinja2テンプレート
- **医療免責**: このアプリは医療判断を行わない。あくまでアラート・気づきのツール

---

## チーム構成

| 担当 | 役割 |
|---|---|
| A | サーバー・DB・認証・Flask基盤 |
| B | 親（患者）画面 |
| **C（ゆーすけ）** | **子（見守り担当）画面** |

---

## ブランチ運用

- `main` — 保護済み、direct push禁止
- `feature/server` — A担当
- `feature/parent` — B担当
- `feature/watcher` — C担当（メイン開発ブランチ）
- `feature/watcher-color-tune` — カラー調整検討ブランチ

---

## 優先スキル

このプロジェクトでは以下のスキルを積極的に使う:

- **frontend-design** — UIコンポーネント・画面作成時
- **ui-ux-pro-max** — デザイン評価・カラー・UXレビュー時
- **api-design** — エンドポイント設計・api_contract確認時
- **security-review** — 認証・フォーム・DBアクセスのレビュー時
- **design-system** — デザイントークン・CSS変数の整合性確認時
- **frontend-patterns** — Jinja2テンプレート・JS実装のパターン参照時
- **healthcare-cdss-patterns** — アラートロジック・スコアリング設計時
- **healthcare-phi-compliance** — 患者データの取り扱い・プライバシー確認時
- **hipaa-compliance** — 医療データセキュリティ要件確認時
- **accessibility** — WCAG対応・高齢者向けUI確認時
- **git-workflow** — チーム開発・ブランチ運用・コンフリクト解消時
- **finishing-a-development-branch** — ブランチ完成時のチェックリスト
- **systematic-debugging** — Flaskのバグを体系的に潰す時
- **flask-api-development** — Flask Blueprint・ルーティング・認証実装時
- **flask-python** — Flaskベストプラクティス・application factory参照時
- **sqlite-database-expert** — SQLite設計・クエリ・マイグレーション時
- **accessibility-a11y** — WCAG対応・アクセシブルなHTML実装時
- **code-review-quality** — コードレビュー・品質チェック時

---

## コーディング規約

### テンプレート（Jinja2）
- `templates/watcher/` — C担当の画面
- `templates/auth/` — 認証画面（B/C共同）
- `{% extends "base.html" %}` を使うこと
- CSS は `{{ url_for('static', filename='css/watcher.css') }}` で参照

### CSS
- CSS変数は `:root` で一元管理（`watcher.css` 冒頭）
- クラス命名: BEM準拠、プレフィックス `w-`（watcher）
- アラートクラス: `.alert-0` 〜 `.alert-3`（base.cssと共有予定）
- タッチターゲット: `min-height: 60px`

### Python / Flask
- ルートは `blueprints/watcher.py` に定義
- DBアクセスは `models/` 経由
- テンプレートに渡す変数は `api_contract.md` の仕様に従う

---

## 設計ドキュメント

| ファイル | 内容 |
|---|---|
| `docs/api_contract.md` | 全エンドポイント・テンプレートコンテキスト仕様 |
| `docs/project_structure.md` | フォルダ構成・起動手順 |
| `docs/sprint_plan_v3.md` | 4日間スプリント計画 |
| `docs/PROJECT_INDEX.md` | ドキュメント索引 |

---

## 医療UIの注意点

- アラートは色だけでなく **絵文字 + テキスト** で判別できるようにする（色覚対応）
- 電話ボタンは `min-height: 60px` 以上（高齢者も操作するため）
- 警戒（level 3）・注意（level 2）時のみ電話ボタンを表示
- 判定ロジックはフロントで行わない（サーバーから `alert_level` を受け取る）

---

## スプリント進捗（C担当）

### Day 1（2026-04-27）✅
- [x] watcher.css（デザインシステム）
- [x] dashboard.html（親一覧）
- [x] parent_detail.html（親詳細）
- [x] register_watcher.html（トークン経由登録）
- [x] login.html（共通ログイン）

### Day 2〜4（予定）
- [ ] Flask Blueprint 接続（Aの環境待ち）
- [ ] 実データとの結合
- [ ] エラー画面（404/500）
- [ ] レスポンシブ最終調整
