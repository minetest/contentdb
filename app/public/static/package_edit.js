// @author rubenwardy
// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

"use strict";

function hide(sel) {
	document.querySelectorAll(sel).forEach(x => x.classList.add("d-none"));
}

function show(sel) {
	document.querySelectorAll(sel).forEach(x => x.classList.remove("d-none"));
}


window.addEventListener("load", () => {
	const typeEle = document.getElementById("type");
	typeEle.addEventListener("change", () => {
		show(".not_mod, .not_game, .not_txp");
		hide(".not_" + typeEle.value.toLowerCase());
	})
	show(".not_mod, .not_game, .not_txp");
	hide(".not_" + typeEle.value.toLowerCase());

	const forumsField = document.getElementById("forums");
	forumsField.addEventListener("paste", function(e) {
		try {
			const pasteData = e.clipboardData.getData('text');
			const url = new URL(pasteData);
			if (url.hostname === "forum.minetest.net") {
				forumsField.value = url.searchParams.get("t");
				e.preventDefault();
			}
		} catch (e) {
			console.log("Not a URL");
		}
	});

	const openForums = document.getElementById("forums-button");
	openForums.addEventListener("click", () => {
		window.open("https://forum.minetest.net/viewtopic.php?t=" + forumsField.value, "_blank");
	});

	let hint = null;
	function showHint(ele, text) {
		if (hint) {
			hint.remove();
		}

		hint = document.createElement("div");
		hint.classList.add("alert");
		hint.classList.add("alert-warning");
		hint.classList.add("my-1");
		hint.innerHTML = text;

		ele.parentNode.appendChild(hint);
	}

	let hint_mtmods = `Tip:
		Don't include <i>Minetest</i>, <i>mod</i>, or <i>modpack</i> anywhere in the short description.
		It is unnecessary and wastes characters.`;

	let hint_thegame = `Tip:
		It's obvious that this adds something to Minetest,
		there's no need to use phrases such as \"adds X to the game\".`;

	const shortDescField = document.getElementById("short_desc");

	function handleShortDescChange() {
		const val = shortDescField.value.toLowerCase();
		if (val.indexOf("minetest") >= 0 || val.indexOf("mod") >= 0 ||
				val.indexOf("modpack") >= 0 || val.indexOf("mod pack") >= 0) {
			showHint(shortDescField, hint_mtmods);
		} else if (val.indexOf("the game") >= 0) {
			showHint(shortDescField, hint_thegame);
		} else if (hint) {
			hint.remove();
			hint = null;
		}
	}

	shortDescField.addEventListener("change", handleShortDescChange);
	shortDescField.addEventListener("paste", handleShortDescChange);
	shortDescField.addEventListener("keyup", handleShortDescChange);
})
