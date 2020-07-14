/*!
 * Tag Selector plugin for jQuery: Facilitates selecting multiple tags by extending jQuery UI Autocomplete.
 * You may use Tag Selector under the terms of either the MIT License or the GNU General Public License (GPL) Version 2.
 * https://petprojects.googlecode.com/svn/trunk/MIT-LICENSE.txt
 * https://petprojects.googlecode.com/svn/trunk/GPL-LICENSE.txt
 */
(function($) {
	function hide_error(input) {
		var err = input.parent().parent().find(".invalid-remaining");
		err.hide();
	}

	function show_error(input, msg) {
		var err = input.parent().parent().find(".invalid-remaining");
		console.log(err.length);
		err.text(msg);
		err.show();
	}

	$.fn.selectSelector = function(source, select) {
		return this.each(function() {
			var selector = $(this),
				input = $('input[type=text]', this);

			selector.click(function() { input.focus(); })
				.delegate('.badge a', 'click', function() {
					var id = $(this).parent().data("id");
					select.find("option[value=" + id + "]").attr("selected", false)
					recreate();
				});

			function addTag(id, text) {
				$('<span class="badge badge-pill badge-primary"/>')
					.text(text + ' ')
					.data("id", id)
					.append('<a>x</a>')
					.insertBefore(input);
				input.attr("placeholder", null);
				select.find("option[value='" + id + "']").attr("selected", "selected")
				hide_error(input);
			}

			function recreate() {
				selector.find("span").remove();
				select.find("option").each(function() {
					if (this.hasAttribute("selected")) {
						addTag(this.getAttribute("value"), this.innerText);
					}
				});
			}
			recreate();

			input.focusout(function(e) {
				var value = input.val().trim()
				if (value != "") {
					show_error(input, "Please select an existing tag, it;s not possible to add custom ones.");
				}
			})

			input.keydown(function(e) {
					if (e.keyCode === $.ui.keyCode.TAB && $(this).data('ui-autocomplete').menu.active)
						e.preventDefault();
				})
				.autocomplete({
					minLength: 0,
					source: source,
					select: function(event, ui) {
						addTag(ui.item.id, ui.item.toString());
						input.val("");
						return false;
					}
				}).focus(function() {
					// The following works only once.
					// $(this).trigger('keydown.autocomplete');
					// As suggested by digitalPBK, works multiple times
					// $(this).data("autocomplete").search($(this).val());
					// As noted by Jonny in his answer, with newer versions use uiAutocomplete
					$(this).data("ui-autocomplete").search($(this).val());
				});

			input.data('ui-autocomplete')._renderItem = function(ul, item) {
					return $('<li/>')
						.data('item.autocomplete', item)
						.append($('<a/>').text(item.toString()))
						.appendTo(ul);
				};

			input.data('ui-autocomplete')._resizeMenu = function(ul, item) {
					var ul = this.menu.element;
					ul.outerWidth(Math.max(
						ul.width('').outerWidth(),
						selector.outerWidth()
					));
				};
		});
	}

	$.fn.csvSelector = function(source, name, result, allowSlash) {
		return this.each(function() {
				var selector = $(this),
					input = $('input[type=text]', this);

				var selected = [];
				var lookup = {};
				for (var i = 0; i < source.length; i++) {
					lookup[source[i].id] = source[i];
				}

				selector.click(function() { input.focus(); })
					.delegate('.badge a', 'click', function() {
						var id = $(this).parent().data("id");
						for (var i = 0; i < selected.length; i++) {
							if (selected[i] == id) {
								selected.splice(i, 1);
							}
						}
						recreate();
					});

				function selectItem(id) {
					for (var i = 0; i < selected.length; i++) {
						if (selected[i] == id) {
							return false;
						}
					}
					selected.push(id);
					return true;
				}

				function addTag(id, value) {
					var tag = $('<span class="badge badge-pill badge-primary"/>')
						.text(value)
						.data("id", id)
						.append(' <a>x</a>')
						.insertBefore(input);

					input.attr("placeholder", null);
					hide_error(input);
				}

				function recreate() {
					selector.find("span").remove();
					for (var i = 0; i < selected.length; i++) {
						var value = lookup[selected[i]] || { value: selected[i] };
						addTag(selected[i], value.value);
					}
					result.val(selected.join(","))
				}

				function readFromResult() {
					selected = [];
					var selected_raw = result.val().split(",");
					for (var i = 0; i < selected_raw.length; i++) {
						var raw = selected_raw[i].trim();
						if (lookup[raw] || raw.match(/^([a-z0-9_]+)$/)) {
							selected.push(raw);
						}
					}

					recreate();
				}
				readFromResult();

				result.change(readFromResult);

				input.focusout(function() {
					var item = input.val();
					if (item.length == 0) {
						input.data("ui-autocomplete").search("");
					} else if (item.match(/^([a-z0-9_]+)$/)) {
						selectItem(item);
						recreate();
						input.val("");
					}
					return true;
				});

				input.keydown(function(e) {
						if (e.keyCode === $.ui.keyCode.TAB && $(this).data('ui-autocomplete').menu.active)
							e.preventDefault();
						else if (e.keyCode === $.ui.keyCode.COMMA) {
							var item = input.val();
							if (item.length == 0) {
								input.data("ui-autocomplete").search("");
							} else if (item.match(/^([a-z0-9_]+)$/)) {
								selectItem(item);
								recreate();
								input.val("");
							} else {
								show_error(input, "Only lowercase alphanumeric and number names allowed.");
							}
							e.preventDefault();
							return true;
						} else if (e.keyCode === $.ui.keyCode.BACKSPACE) {
							if (input.val() == "") {
								var item = selected[selected.length - 1];
								selected.splice(selected.length - 1, 1);
								recreate();
								if (!(item.indexOf("/") > 0))
									input.val(item);
								e.preventDefault();
								return true;
							}
						}
					})
					.autocomplete({
						minLength: 0,
						source: source,
						select: function(event, ui) {
							selectItem(ui.item.id);
							recreate();
							input.val("");
							return false;
						}
					});

				input.data('ui-autocomplete')._renderItem = function(ul, item) {
						return $('<li/>')
							.data('item.autocomplete', item)
							.append($('<a/>').text(item.toString()))
							.appendTo(ul);
					};

				input.data('ui-autocomplete')._resizeMenu = function(ul, item) {
						var ul = this.menu.element;
						ul.outerWidth(Math.max(
							ul.width('').outerWidth(),
							selector.outerWidth()
						));
					};
			});
	}

	$(function() {
		$(".multichoice_selector").each(function() {
			var ele = $(this);
			var sel = ele.parent().find("select");
			sel.hide();

			var options = [];
			sel.find("option").each(function() {
				var text = $(this).text();
				options.push({
					id: $(this).attr("value"),
					value: text,
					selected: $(this).attr("selected") ? true : false,
					toString: function() { return text; },
				});
			});

			ele.selectSelector(options, sel);
		});

		$(".metapackage_selector").each(function() {
			var input = $(this).parent().children("input[type='text']");
			input.hide();
			$(this).csvSelector(meta_packages, input.attr("name"), input);
		});

		$(".deps_selector").each(function() {
			var input = $(this).parent().children("input[type='text']");
			input.hide();
			$(this).csvSelector(all_packages, input.attr("name"), input);
		});
	});
})(jQuery);
