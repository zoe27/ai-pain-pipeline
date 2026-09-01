#!/usr/bin/env python3
"""
DemandRadar Review Dashboard

Review 知乎回答草稿 + 一键发布（Cookie 方式）

启动：
    python3 review_dashboard.py --growth-id growth_zhihu_2026-09-01_001

访问：http://localhost:8081
"""

import argparse
import json
import time
import random
import webbrowser
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import requests
from flask import Flask, jsonify, request, Response

app = Flask(__name__)

GROWTH_ID = None
RUN_DIR = None

# ---------------------------------------------------------------------------
# Zhihu Publisher
# ---------------------------------------------------------------------------

class ZhihuPublisher:
    ANSWER_URL = "https://www.zhihu.com/api/v4/questions/{question_id}/answers"
    HEADERS_BASE = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/126.0.0.0 Safari/537.36",
        "Referer": "https://www.zhihu.com/",
        "Origin": "https://www.zhihu.com",
        "x-requested-with": "fetch",
        "x-zse-93": "101_3_3.0",
    }

    def __init__(self, cookies: dict):
        self.session = requests.Session()
        self.session.cookies.update(cookies)
        self.session.headers.update(self.HEADERS_BASE)

    def publish(self, question_id: str, content: str) -> dict:
        url = self.ANSWER_URL.format(question_id=question_id)
        payload = {
            "content": content,
            "reward_setting": {"can_reward": False, "tagline": ""},
            "excerpt": content[:100].replace("\n", " "),
        }
        time.sleep(random.uniform(2, 4))
        try:
            resp = self.session.post(url, json=payload, timeout=20)
            if resp.status_code in (200, 201):
                data = resp.json()
                answer_id = str(data.get("id", ""))
                return {
                    "success": True,
                    "answer_id": answer_id,
                    "url": f"https://www.zhihu.com/question/{question_id}/answer/{answer_id}",
                    "error": None,
                }
            else:
                return {"success": False, "answer_id": None, "url": None,
                        "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}
        except Exception as e:
            return {"success": False, "answer_id": None, "url": None, "error": str(e)}


class ZhihuAnswerChecker:
    """Detect whether the logged-in account already answered a question."""

    def __init__(self, cookies: dict):
        self.session = requests.Session()
        for name, value in cookies.items():
            if value is not None:
                self.session.cookies.set(str(name), str(value), domain=".zhihu.com")
        try:
            from helpers.zhihu_answer_status import make_session, check_question_answered, check_questions_answered
        except ImportError:
            from zhihu_answer_status import make_session, check_question_answered, check_questions_answered
        self._check_question = check_question_answered
        self._check_questions = check_questions_answered
        make_session(session=self.session)

    def check_question(self, question_id: str) -> dict:
        return self._check_question(self.session, question_id)

    def check_questions(self, question_ids: List[str]) -> Dict[str, dict]:
        return self._check_questions(question_ids, session=self.session)

# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_answers() -> dict:
    with open(RUN_DIR / "g4_zhihu_answers.json", encoding="utf-8") as f:
        return json.load(f)

def save_answers(data: dict):
    with open(RUN_DIR / "g4_zhihu_answers.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_cookies() -> dict:
    cookie_path = Path("configs/zhihu.cookies.json")
    if not cookie_path.exists():
        return {}
    with open(cookie_path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {
            item["name"]: item["value"]
            for item in data
            if isinstance(item, dict) and item.get("name") and item.get("value") is not None
        }
    if "cookies" in data and isinstance(data["cookies"], dict):
        return data["cookies"]
    return data if isinstance(data, dict) else {}

# ---------------------------------------------------------------------------
# HTML — pure static, all data loaded via /api/answers
# ---------------------------------------------------------------------------

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DemandRadar Review</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Helvetica Neue",Arial,sans-serif;background:#f0f2f5;color:#1a1a1a}
.topbar{background:#fff;border-bottom:1px solid #e5e7eb;padding:14px 28px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100}
.topbar-title{font-size:17px;font-weight:600;color:#111}
.topbar-meta{font-size:13px;color:#888}
.badge{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:500}
.badge-urgent{background:#fee2e2;color:#b91c1c}
.badge-high{background:#fef3c7;color:#b45309}
.badge-medium{background:#e0f2fe;color:#0369a1}
.badge-low{background:#f3f4f6;color:#6b7280}
.badge-published{background:#dcfce7;color:#166534}
.badge-answered{background:#ffedd5;color:#c2410c}
.badge-failed{background:#fecaca;color:#991b1b}
.badge-pending,.badge-skipped{background:#f3f4f6;color:#374151}
.layout{display:flex;min-height:calc(100vh - 57px)}
.sidebar{width:300px;flex-shrink:0;background:#fff;border-right:1px solid #e5e7eb;overflow-y:auto;max-height:calc(100vh - 57px);position:sticky;top:57px}
.sidebar-item{padding:14px 16px;border-bottom:1px solid #f3f4f6;cursor:pointer;transition:background .15s}
.sidebar-item:hover{background:#f9fafb}
.sidebar-item.active{background:#eff6ff;border-left:3px solid #2563eb}
.q-title{font-size:13px;font-weight:500;color:#111;margin-bottom:6px;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.q-meta{display:flex;align-items:center;gap:6px;font-size:12px;color:#888;flex-wrap:wrap}
.score-dot{width:8px;height:8px;border-radius:50%;display:inline-block;background:#10b981}
.score-dot.mid{background:#f59e0b}.score-dot.low{background:#d1d5db}
.main{flex:1;padding:24px 28px;overflow-y:auto}
.card{background:#fff;border-radius:10px;padding:24px;margin-bottom:20px;box-shadow:0 1px 3px rgba(0,0,0,.07)}
.card-title{font-size:15px;font-weight:600;color:#374151;margin-bottom:14px;display:flex;align-items:center;gap:8px}
.question-link{font-size:15px;font-weight:600;color:#2563eb;text-decoration:none;line-height:1.4}
.question-link:hover{text-decoration:underline}
.question-meta{margin-top:8px;font-size:13px;color:#6b7280;display:flex;gap:16px;flex-wrap:wrap}
.answer-editor{width:100%;min-height:340px;padding:14px;font-size:14px;line-height:1.7;border:1px solid #e5e7eb;border-radius:8px;resize:vertical;font-family:inherit;outline:none;transition:border-color .2s;background:#fafafa}
.answer-editor:focus{border-color:#2563eb;background:#fff}
.answer-preview{font-size:14px;line-height:1.8;color:#374151;padding:14px;background:#fafafa;border:1px solid #e5e7eb;border-radius:8px;min-height:200px}
.answer-preview h2,.answer-preview h3{margin:12px 0 6px;font-size:15px}
.answer-preview strong{font-weight:600}
.answer-preview ul{padding-left:20px;margin:6px 0}
.answer-preview li{margin:3px 0}
.answer-preview hr{border:none;border-top:1px solid #e5e7eb;margin:14px 0}
.tab-row{display:flex;border-bottom:1px solid #e5e7eb;margin-bottom:14px}
.tab{padding:8px 18px;font-size:13px;cursor:pointer;color:#6b7280;border-bottom:2px solid transparent;margin-bottom:-1px;transition:color .15s}
.tab.active{color:#2563eb;border-bottom-color:#2563eb;font-weight:500}
.actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:16px}
.btn{padding:9px 18px;font-size:14px;font-weight:500;border-radius:7px;cursor:pointer;border:none;transition:background .15s,opacity .15s}
.btn:disabled{opacity:.5;cursor:not-allowed}
.btn-primary{background:#2563eb;color:#fff}.btn-primary:hover:not(:disabled){background:#1d4ed8}
.btn-skip{background:#f3f4f6;color:#6b7280}.btn-skip:hover:not(:disabled){background:#e5e7eb}
.btn-link{background:#eff6ff;color:#2563eb;text-decoration:none;display:inline-flex;align-items:center;padding:9px 18px;font-size:14px;font-weight:500;border-radius:7px}
.btn-link:hover{background:#dbeafe}
.status-msg{font-size:13px;padding:8px 14px;border-radius:6px;margin-top:10px;display:none}
.status-msg.success{background:#dcfce7;color:#166534;display:block}
.status-msg.error{background:#fee2e2;color:#991b1b;display:block}
.status-msg.loading{background:#e0f2fe;color:#0369a1;display:block}
.stat-row{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px}
.stat-box{background:#fff;border-radius:8px;padding:14px 20px;box-shadow:0 1px 3px rgba(0,0,0,.07);min-width:110px;text-align:center}
.stat-box .num{font-size:26px;font-weight:700;color:#111}
.stat-box .lbl{font-size:12px;color:#888;margin-top:3px}
.word-count{font-size:12px;color:#9ca3af;text-align:right;margin-top:4px}
.hint{margin-top:10px;font-size:12px;color:#9ca3af}
.loading-state,.empty-state{text-align:center;color:#9ca3af;padding:60px 20px;font-size:15px}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-title">📡 DemandRadar Review</div>
  <div class="topbar-meta" id="topbar-meta">加载中...</div>
</div>

<div class="layout">
  <div class="sidebar" id="sidebar"><div class="loading-state">加载中...</div></div>
  <div class="main" id="main"><div class="loading-state">加载中...</div></div>
</div>

<script>
let answers = [];
let currentIdx = 0;
let checkingAnswered = false;

function isAlreadyAnswered(a) {
  return !!(a.existing_answer && a.existing_answer.answered);
}

function displayStatus(a) {
  if (a.publish_status === 'published') return 'published';
  if (a.publish_status === 'skipped') return 'skipped';
  if (a.publish_status === 'failed') return 'failed';
  if (isAlreadyAnswered(a)) return 'answered';
  return a.publish_status || 'pending';
}

function statusLabel(status) {
  const labels = {
    pending: '待发布',
    published: '已发布',
    skipped: '已跳过',
    failed: '失败',
    answered: '已在知乎回答',
  };
  return labels[status] || status;
}

// ── load data ──────────────────────────────────────────────────────────────
async function init() {
  document.getElementById('topbar-meta').textContent = '加载草稿...';
  const resp = await fetch('/api/answers');
  const data = await resp.json();
  answers = data.zhihu_answers || [];

  document.getElementById('topbar-meta').textContent =
    data.growth_id + ' · ' + answers.length + ' 条草稿 · ' + data.product_title + ' · 检测知乎回答状态中...';

  await refreshAnsweredStatus();

  document.getElementById('topbar-meta').textContent =
    data.growth_id + ' · ' + answers.length + ' 条草稿 · ' + data.product_title;

  document.getElementById('main').innerHTML = '';
  renderSidebar();
  renderStats(answers);
  if (answers.length > 0) renderCard(currentIdx);
}

async function refreshAnsweredStatus() {
  if (checkingAnswered) return;
  checkingAnswered = true;
  try {
    const resp = await fetch('/api/check-answered', { method: 'POST' });
    const data = await resp.json();
    if (data.success) {
      answers = data.zhihu_answers || answers;
    }
  } catch (e) {
    console.warn('check-answered failed', e);
  } finally {
    checkingAnswered = false;
  }
}

// ── sidebar ────────────────────────────────────────────────────────────────
function renderSidebar() {
  const sb = document.getElementById('sidebar');
  if (!answers.length) { sb.innerHTML = '<div class="empty-state">暂无草稿</div>'; return; }
  sb.innerHTML = answers.map((a, i) => {
    const score = a.opportunity_score || 0;
    const dotCls = score >= 90 ? '' : score >= 75 ? 'mid' : 'low';
    const pri = a.metadata?.publish_recommendation?.priority || 'medium';
    const status = displayStatus(a);
    return `<div class="sidebar-item${i === 0 ? ' active' : ''}" data-idx="${i}">
      <div class="q-title">${escHtml(a.question_title)}</div>
      <div class="q-meta">
        <span class="score-dot ${dotCls}"></span>
        <span>Score ${score}</span>
        <span class="badge badge-${pri}">${pri}</span>
        <span class="badge badge-${status}" id="sb-status-${i}">${statusLabel(status)}</span>
      </div>
    </div>`;
  }).join('');

  sb.querySelectorAll('.sidebar-item').forEach(el => {
    el.addEventListener('click', () => {
      currentIdx = parseInt(el.dataset.idx);
      sb.querySelectorAll('.sidebar-item').forEach(e => e.classList.remove('active'));
      el.classList.add('active');
      renderCard(currentIdx);
      document.getElementById('main').scrollTop = 0;
    });
  });
}

// ── stats bar ──────────────────────────────────────────────────────────────
function renderStats(list) {
  const counts = {pending:0, published:0, failed:0, skipped:0, answered:0};
  list.forEach(a => {
    const s = displayStatus(a);
    counts[s] = (counts[s]||0)+1;
  });
  const existing = document.getElementById('stat-row');
  if (existing) existing.remove();
  document.getElementById('main').insertAdjacentHTML('afterbegin', `
    <div class="stat-row" id="stat-row">
      <div class="stat-box"><div class="num">${list.length}</div><div class="lbl">总草稿</div></div>
      <div class="stat-box"><div class="num">${counts.pending}</div><div class="lbl">待发布</div></div>
      <div class="stat-box"><div class="num" style="color:#ea580c">${counts.answered}</div><div class="lbl">已在知乎回答</div></div>
      <div class="stat-box"><div class="num" style="color:#16a34a">${counts.published}</div><div class="lbl">本工具发布</div></div>
      <div class="stat-box"><div class="num" style="color:#b91c1c">${counts.failed}</div><div class="lbl">失败</div></div>
      <div class="stat-box"><button class="btn btn-skip" id="recheck-btn" style="margin-top:6px">🔄 重新检测</button></div>
    </div>`);
  document.getElementById('recheck-btn').addEventListener('click', async () => {
    document.getElementById('recheck-btn').disabled = true;
    document.getElementById('recheck-btn').textContent = '检测中...';
    await refreshAnsweredStatus();
    renderSidebar();
    renderStats(answers);
    renderCard(currentIdx);
    document.getElementById('recheck-btn').disabled = false;
    document.getElementById('recheck-btn').textContent = '🔄 重新检测';
  });
}

// ── card ───────────────────────────────────────────────────────────────────
function renderCard(idx) {
  const a = answers[idx];
  const pri = a.metadata?.publish_recommendation?.priority || 'medium';
  const notes = a.metadata?.publish_recommendation?.notes || '';
  const text = a.generated_answer?.text || '';
  const wc = a.generated_answer?.word_count || text.length;
  const status = displayStatus(a);
  const srcMeta = a.source_metadata || {};
  const existing = a.existing_answer || {};

  let actionHtml = '';
  if (status === 'published') {
    actionHtml = `<span class="badge badge-published" style="font-size:13px;padding:6px 14px">✓ 本工具已发布</span>
      ${a.published_url ? `<a class="btn-link" href="${escAttr(a.published_url)}" target="_blank">查看已发布回答 →</a>` : ''}`;
  } else if (status === 'answered') {
    actionHtml = `<span class="badge badge-answered" style="font-size:13px;padding:6px 14px">✓ 已在知乎回答</span>
      ${existing.url ? `<a class="btn-link" href="${escAttr(existing.url)}" target="_blank">查看已有回答 →</a>` : ''}
      <button class="btn btn-skip" id="skip-btn">标记跳过</button>`;
  } else {
    actionHtml = `
      <button class="btn btn-primary" id="pub-btn">🚀 发布到知乎</button>
      <button class="btn btn-skip" id="skip-btn">跳过</button>`;
  }

  const cardHtml = `
    <div class="card" id="q-card">
      <div class="card-title">
        💬 原问题
        <span class="badge badge-${pri}">${pri}</span>
        <span style="font-size:13px;color:#888;margin-left:auto">机会分 ${a.opportunity_score || 0}</span>
      </div>
      <a class="question-link" href="${escAttr(a.question_url)}" target="_blank">${escHtml(a.question_title)}</a>
      ${a.question_detail ? `<p style="margin-top:10px;font-size:13px;color:#6b7280;line-height:1.6">${escHtml(a.question_detail)}</p>` : ''}
      <div class="question-meta">
        <span>📎 <a href="${escAttr(a.question_url)}" target="_blank" style="color:#2563eb">在知乎查看原帖 →</a></span>
        ${srcMeta.view_count ? `<span>👁 ${srcMeta.view_count} 浏览</span>` : ''}
        ${srcMeta.answer_count ? `<span>💬 ${srcMeta.answer_count} 回答</span>` : ''}
        ${existing.checked_at ? `<span>🔍 检测于 ${escHtml(existing.checked_at.slice(0, 19).replace('T', ' '))}</span>` : ''}
        <span>🏷 ${escHtml(a.cluster_id || '')}</span>
      </div>
      ${status === 'answered' ? `<p style="margin-top:10px;font-size:13px;color:#c2410c;background:#fff7ed;padding:10px 12px;border-radius:8px">该问题下你的知乎账号已有回答，无需重复发布。可点击查看已有回答，或编辑草稿后手动更新。</p>` : ''}
    </div>

    <div class="card" id="draft-card">
      <div class="card-title">✍️ 回答草稿</div>
      <div class="tab-row">
        <div class="tab active" id="tab-edit">编辑</div>
        <div class="tab" id="tab-preview">预览</div>
      </div>
      <div id="edit-pane">
        <textarea class="answer-editor" id="editor">${escHtml(text)}</textarea>
        <div class="word-count" id="wc">${wc} 字</div>
      </div>
      <div id="preview-pane" style="display:none">
        <div class="answer-preview" id="preview-content"></div>
      </div>
      <div class="actions">${actionHtml}</div>
      <div class="status-msg" id="status-msg"></div>
      ${notes ? `<p class="hint">💡 ${escHtml(notes)}</p>` : ''}
    </div>`;

  // Replace everything after stat-row
  const main = document.getElementById('main');
  const existingCard = document.getElementById('q-card');
  if (existingCard) {
    existingCard.remove();
    document.getElementById('draft-card')?.remove();
  }
  main.insertAdjacentHTML('beforeend', cardHtml);

  // Bind events
  document.getElementById('editor').addEventListener('input', () => {
    document.getElementById('wc').textContent = document.getElementById('editor').value.length + ' 字';
  });
  document.getElementById('tab-edit').addEventListener('click', function() {
    this.classList.add('active'); document.getElementById('tab-preview').classList.remove('active');
    document.getElementById('edit-pane').style.display = '';
    document.getElementById('preview-pane').style.display = 'none';
  });
  document.getElementById('tab-preview').addEventListener('click', function() {
    this.classList.add('active'); document.getElementById('tab-edit').classList.remove('active');
    document.getElementById('edit-pane').style.display = 'none';
    document.getElementById('preview-pane').style.display = '';
    document.getElementById('preview-content').innerHTML =
      renderMarkdown(document.getElementById('editor').value);
  });
  if (status !== 'published' && status !== 'answered') {
    document.getElementById('pub-btn').addEventListener('click', () => publishAnswer(idx, a.answer_id, a.question_id));
    document.getElementById('skip-btn').addEventListener('click', () => skipAnswer(idx, a.answer_id));
  } else if (status === 'answered') {
    document.getElementById('skip-btn').addEventListener('click', () => skipAnswer(idx, a.answer_id));
  }
}

// ── publish ────────────────────────────────────────────────────────────────
async function publishAnswer(idx, answerId, questionId) {
  const btn = document.getElementById('pub-btn');
  const text = document.getElementById('editor').value.trim();
  if (!text) { showStatus('error', '回答内容不能为空'); return; }

  btn.disabled = true;
  btn.textContent = '发布中...';
  showStatus('loading', '正在发布到知乎，请稍候...');

  try {
    const resp = await fetch('/api/publish', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({answer_id: answerId, question_id: questionId, content: text}),
    });
    const data = await resp.json();
    if (data.success) {
      answers[idx].publish_status = 'published';
      answers[idx].published_url = data.url;
      updateSidebarStatus(idx, 'published');
      showStatus('success', `✅ 发布成功！<a href="${data.url}" target="_blank" style="color:#166534">查看回答 →</a>`);
      btn.style.display = 'none';
    } else {
      showStatus('error', '❌ 发布失败：' + data.error);
      btn.disabled = false;
      btn.textContent = '🚀 发布到知乎';
    }
  } catch (e) {
    showStatus('error', '❌ 网络错误：' + e.message);
    btn.disabled = false;
    btn.textContent = '🚀 发布到知乎';
  }
}

async function skipAnswer(idx, answerId) {
  await fetch('/api/skip', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({answer_id: answerId})});
  answers[idx].publish_status = 'skipped';
  updateSidebarStatus(idx, 'skipped');
  showStatus('success', '已跳过');
  if (idx + 1 < answers.length) setTimeout(() => {
    document.querySelectorAll('.sidebar-item')[idx + 1].click();
  }, 600);
}

function updateSidebarStatus(idx, status) {
  const el = document.getElementById('sb-status-' + idx);
  if (el) { el.className = 'badge badge-' + status; el.textContent = statusLabel(status); }
}

function showStatus(type, msg) {
  const el = document.getElementById('status-msg');
  el.className = 'status-msg ' + type;
  el.innerHTML = msg;
}

// ── markdown renderer ──────────────────────────────────────────────────────
function renderMarkdown(text) {
  return escHtml(text)
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/[*][*](.+?)[*][*]/g, '<strong>$1</strong>')
    .replace(/^---$/gm, '<hr>')
    .replace(/^[-•] (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, m => '<ul>' + m + '</ul>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n/g, '<br>');
}

// ── utils ──────────────────────────────────────────────────────────────────
function escHtml(s) {
  return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
function escAttr(s) { return escHtml(s); }

init();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return Response(HTML, mimetype="text/html")

@app.route("/api/answers")
def api_answers():
    return jsonify(load_answers())

@app.route("/api/check-answered", methods=["POST"])
def api_check_answered():
    cookies = load_cookies()
    if not cookies:
        return jsonify({
            "success": False,
            "error": "未找到 Cookie 文件，无法检测知乎回答状态",
        }), 400

    data = load_answers()
    pending = [
        a for a in data["zhihu_answers"]
        if a.get("publish_status") not in ("published", "skipped")
    ]
    question_ids = [a["question_id"] for a in pending]

    checker = ZhihuAnswerChecker(cookies)
    results = checker.check_questions(question_ids)

    answered_count = 0
    for answer in data["zhihu_answers"]:
        qid = answer["question_id"]
        if qid not in results:
            continue
        answer["existing_answer"] = results[qid]
        if results[qid].get("answered"):
            answered_count += 1

    save_answers(data)
    return jsonify({
        "success": True,
        "checked": len(question_ids),
        "already_answered": answered_count,
        "zhihu_answers": data["zhihu_answers"],
    })

@app.route("/api/publish", methods=["POST"])
def api_publish():
    body = request.get_json()
    answer_id   = body["answer_id"]
    question_id = body["question_id"]
    content     = body["content"]

    cookies = load_cookies()
    if not cookies:
        return jsonify({"success": False,
                        "error": "未找到 Cookie 文件，请创建 configs/zhihu.cookies.json"}), 400

    result = ZhihuPublisher(cookies).publish(question_id, content)

    data = load_answers()
    for a in data["zhihu_answers"]:
        if a["answer_id"] == answer_id:
            a["publish_status"] = "published" if result["success"] else "failed"
            a["published_at"]   = datetime.now().isoformat() if result["success"] else None
            a["published_url"]  = result.get("url")
            a["generated_answer"]["text"] = content
            break
    save_answers(data)
    return jsonify(result)

@app.route("/api/skip", methods=["POST"])
def api_skip():
    body = request.get_json()
    data = load_answers()
    for a in data["zhihu_answers"]:
        if a["answer_id"] == body["answer_id"]:
            a["publish_status"] = "skipped"
            break
    save_answers(data)
    return jsonify({"success": True})

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    global GROWTH_ID, RUN_DIR

    parser = argparse.ArgumentParser(description="DemandRadar Review Dashboard")
    parser.add_argument("--growth-id", required=True, help="Growth run ID")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()

    GROWTH_ID = args.growth_id
    RUN_DIR   = Path(f"runs/{GROWTH_ID}")

    if not (RUN_DIR / "g4_zhihu_answers.json").exists():
        print(f"❌ 找不到 runs/{GROWTH_ID}/g4_zhihu_answers.json")
        return

    url = f"http://localhost:{args.port}"
    print(f"\n🚀 DemandRadar Review Dashboard")
    print(f"   Growth ID : {GROWTH_ID}")
    print(f"   访问地址  : {url}\n")

    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=args.port, debug=False)

if __name__ == "__main__":
    main()
