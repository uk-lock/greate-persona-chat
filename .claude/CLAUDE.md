# CLAUDE.md

## プロジェクト概要
偉人の情報をもとにペルソナを生成し、その人物と対話できるアプリ。
単なるチャットアプリではなく、偉人情報の管理、LLMによる対話、外部情報取得・要約・ペルソナ生成のバッチ処理までを扱う。

## 主要な技術
- フロントエンド: Next.js / React / TypeScript
- バックエンド: FastAPI / Python
- DB: PostgreSQL
- 開発環境: Docker Compose / devContainer

## 開発方針
- 小さく作る
- 動くもの優先
- 変更は小さく分ける
- 既存構成を壊さない
- 追加時は README / docs / compose 更新

## 配置方針
- フロントエンド実装: frontend/
- バックエンド実装: backend/
- ドキュメント: docs/

## Claude Code の運用
- 変更前に inspect / plan / verify の順で確認する
- 変更が大きい場合は agent を使い分け、責務を重ねない
- ルールや手順は CLAUDE.md ではなく skills と agent 定義に寄せる
- 重要な前提や再現手順は必要に応じて docs へ残す
