function $(id) {
    return document.getElementById(id);
}

function rankToText(rank) {
    const map = {
        3: "3",
        4: "4",
        5: "5",
        6: "6",
        7: "7",
        8: "8",
        9: "9",
        10: "10",
        11: "J",
        12: "Q",
        13: "K",
        14: "A",
        15: "2",
        16: "SJ",
        17: "BJ"
    };
    return map[rank] || String(rank);
}

function suitToSymbol(suit) {
    switch (suit) {
        case "S": return "♠";
        case "H": return "♥";
        case "D": return "♦";
        case "C": return "♣";
        case "J": return "";
        default: return "?";
    }
}

function cardToDisplayText(card) {
    const rankText = rankToText(card.rank);
    const suitSymbol = suitToSymbol(card.suit);
    if (card.rank >= 16) {
        return rankText;
    }
    return suitSymbol + rankText;
}

function cardIsRed(card) {
    return card.suit === "H" || card.suit === "D";
}

async function fetchAdminState() {
    try {
        const url = `${BACKEND_HTTP_BASE}/admin/state?token=${encodeURIComponent(ADMIN_TOKEN)}`;
        const res = await fetch(url);
        if (!res.ok) {
            $("admin-refresh-status").textContent = "状态：请求失败 " + res.status;
            $("admin-refresh-status").classList.add("status-bad");
            return;
        }
        const data = await res.json();
        renderAdminState(data);
        $("admin-refresh-status").textContent = "状态：已刷新 " + new Date().toLocaleTimeString();
        $("admin-refresh-status").classList.remove("status-bad");
        $("admin-refresh-status").classList.add("status-ok");
    } catch (e) {
        console.error("Admin fetch error:", e);
        $("admin-refresh-status").textContent = "状态：错误";
        $("admin-refresh-status").classList.add("status-bad");
    }
}

function renderAdminState(data) {
    const playersDiv = $("admin-players");
    playersDiv.innerHTML = "";
    const players = data.players || {};

    Object.keys(players).forEach(pid => {
        const p = players[pid];
        const card = document.createElement("div");
        card.classList.add("admin-player-card");

        const title = document.createElement("h3");
        title.textContent = `${pid}（${p.role === "landlord" ? "地主" : "农民"}）`;
        card.appendChild(title);

        const countP = document.createElement("p");
        countP.textContent = `手牌数量：${p.hand_count}`;
        card.appendChild(countP);

        const handDiv = document.createElement("div");
        handDiv.classList.add("admin-player-hand");
        (p.hand || []).forEach(c => {
            const cd = document.createElement("div");
            cd.classList.add("card", "small");
            if (cardIsRed(c)) cd.classList.add("red");
            else cd.classList.add("black");
            cd.textContent = cardToDisplayText(c);
            handDiv.appendChild(cd);
        });
        card.appendChild(handDiv);

        playersDiv.appendChild(card);
    });

    const bottomDiv = $("admin-bottom");
    bottomDiv.innerHTML = "<strong>底牌：</strong>";
    (data.bottom_cards || []).forEach(c => {
        const cd = document.createElement("span");
        cd.classList.add("card", "small");
        if (cardIsRed(c)) cd.classList.add("red");
        else cd.classList.add("black");
        cd.textContent = cardToDisplayText(c);
        bottomDiv.appendChild(cd);
    });

    const infoDiv = $("admin-game-info");
    const lines = [];
    lines.push("地主ID：" + (data.landlord_id || "未确定"));
    lines.push("当前回合：" + (data.current_turn || "-"));
    lines.push("倍数：" + (data.multiplier || 1));
    lines.push("是否结束：" + (data.game_over ? "是" : "否"));
    lines.push("胜利方：" + (data.winner_side || "未产生"));
    infoDiv.innerHTML = lines.join("<br>");

    const historyDiv = $("admin-history");
    historyDiv.innerHTML = "";
    (data.history || []).forEach(h => {
        const div = document.createElement("div");
        div.classList.add("log-entry");
        const textSpan = document.createElement("span");
        textSpan.classList.add("text");
        textSpan.textContent = `${h.player_id}: ${h.cards} (${h.action_type})`;
        div.appendChild(textSpan);
        historyDiv.appendChild(div);
    });
}

window.addEventListener("load", () => {
    // 每秒刷新一次状态
    fetchAdminState();
    setInterval(fetchAdminState, 1000);
});
