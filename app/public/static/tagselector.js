/*!
 * Tag Selector plugin for jQuery: Facilitates selecting multiple tags by extending jQuery UI Autocomplete.
 * You may use Tag Selector under the terms of either the MIT License or the GNU General Public License (GPL) Version 2.
 * https://petprojects.googlecode.com/svn/trunk/MIT-LICENSE.txt
 * https://petprojects.googlecode.com/svn/trunk/GPL-LICENSE.txt
 */
(function($) {
	$.fn.selectSelector = function(source, name, select) {
		return this.each(function() {
				var selector = $(this),
					input = $('input[type=text]', this);

				selector.click(function() { input.focus(); })
					.delegate('.tag a', 'click', function() {
						var id = $(this).parent().data("id");
						for (var i = 0; i < source.length; i++) {
							if (source[i].id == id) {
								source[i].selected = null;
							}
						}
						select.find("option[value=" + id + "]").attr("selected", null)
						recreate();
					});

				function addTag(item) {
					var tag = $('<span class="tag"/>')
						.text(item.toString() + ' ')
						.data("id", item.id)
						.append('<a>x</a>')
						.insertBefore(input);
					input.attr("placeholder", null);
					select.find("option[value=" + item.id + "]").attr("selected", "selected")
				}

				function recreate() {
					selector.find("span").remove();
					for (var i = 0; i < source.length; i++) {
						if (source[i].selected) {
							addTag(source[i]);
						}
					}
				}
				recreate();

				input.keydown(function(e) {
						if (e.keyCode === $.ui.keyCode.TAB && $(this).data('ui-autocomplete').menu.active)
							e.preventDefault();
					})
					.autocomplete({
						minLength: 0,
						source: source,
						select: function(event, ui) {
							addTag(ui.item);
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

				selector.click(function() { input.focus(); })
					.delegate('.tag a', 'click', function() {
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
					var tag = $('<span class="tag"/>')
						.text(value)
						.data("id", id)
						.append(' <a>x</a>')
						.insertBefore(input);

					input.attr("placeholder", null);
				}

				function recreate() {
					selector.find("span").remove();
					for (var i = 0; i < selected.length; i++) {
						var value = source[selected[i]] || selected[i];
						addTag(selected[i], value);
					}
					result.val(selected.join(","))
				}
				recreate();

				input.keydown(function(e) {
						if (e.keyCode === $.ui.keyCode.TAB && $(this).data('ui-autocomplete').menu.active)
							e.preventDefault();
						else if (e.keyCode === $.ui.keyCode.COMMA) {
							var item = input.val();
							if (item.match(/^([a-z0-9_]+)$/)) {
								selectItem(item);
								recreate();
								input.val("");
							} else {
								alert("Only lowercase alphanumeric and number names allowed.");
							}
							e.preventDefault();
							return true;
						} else if (e.keyCode === $.ui.keyCode.BACKSPACE) {
							if (input.val() == "") {
								var item = selected[selected.length - 1];
								selected.splice(selected.length - 1, 1);
								recreate();
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

			console.log(options);
			ele.selectSelector(options, sel.attr("name"), sel);
		});

		$(".metapackage_selector").each(function() {
			var input = $(this).parent().children("input[type='text']");
			input.hide();
			$(this).csvSelector(meta_packages, input.attr("name"), input);
		})
	});
})(jQuery);
