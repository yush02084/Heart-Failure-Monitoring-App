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

## ECC エージェント・コマンド

以下のECCエージェントが有効。状況に応じて積極的に使うこと。

### 計画・設計
| エージェント | 起動タイミング |
|---|---|
| **blueprint** | A/B/C統合・リファクタ・スプリント計画など複数セッションにまたがる作業を整理するとき |
| **council** | DBスキーマ変更・アーキテクチャ選択・設計トレードオフで迷ったとき。4視点で構造的に議論 |
| **architecture-decision-records** | 設計判断をADRとして記録・残すとき（チーム開発での意思決定ログ） |
| **product-capability** | 仕様書・要件定義から実装タスクに落とし込むとき |
| **team-builder** | A/B/C担当に並列エージェントを割り当てて同時作業するとき |

### 実装・開発
| エージェント | 起動タイミング |
|---|---|
| **search-first** | 実装前にパターン・既存コード・ライブラリを調査するとき |
| **tdd-workflow** | テスト駆動でFlaskルート・アラートロジックを実装するとき |
| **python-testing** | pytestのフィクスチャ・モック・カバレッジ設定するとき |
| **e2e-testing** | Playwright E2Eテストでwatcher/parent画面を自動テストするとき |
| **database-migrations** | Alembicマイグレーション設計・ロールバック対応するとき |
| **click-path-audit** | ボタン操作→状態変化の全経路を網羅的にトレースするとき（UIの抜け確認） |
| **codebase-onboarding** | A/B担当向けのコードベース説明資料を自動生成するとき |
| **deployment-patterns** | Docker化・CI/CD・本番デプロイ構成を組むとき |

### 医療・ヘルスケア特化
| エージェント | 起動タイミング |
|---|---|
| **healthcare-emr-patterns** | EMR/EHR設計パターン・臨床安全・エンカウンターモデルを参照するとき |
| **healthcare-eval-harness** | 患者安全評価ハーネスでアラートロジックの品質を自動評価するとき |
| **deep-research** | 心不全モニタリング・WCAG・医療UI設計について深掘りするとき |
| **arxiv** | 心不全モニタリングの最新論文を調査するとき |

### 検証・品質
| エージェント | 起動タイミング |
|---|---|
| **verification-loop** | 実装後に動作・整合性を体系的に検証するとき |
| **santa-method** | 2つの独立エージェントが互いにレビューし合う対立的検証（重要機能のリリース前） |
| **security-scan** | PRマージ前のセキュリティ全体スキャン |
| **agentic-engineering** | タスク分解・ループ・並列処理の設計が必要なとき |
| **agent-sort** | どのスキルを使うか迷ったときの自動ルーティング |

### 使い方
スキルは `skills/` に格納済み。「blueprintを使って計画して」「councilで判断して」と伝えるだけでOK。

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
