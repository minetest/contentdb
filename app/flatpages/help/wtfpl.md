title: WTFPL is a terrible license
toc: False

<div id="warning" class="alert alert-warning">
	<span class="icon_message"></span>

	Please reconsider the choice of WTFPL as a license.

	<script src="/static/libs/jquery.min.js"></script>
	<script>
		// @author rubenwardy
		// @license magnet:?xt=urn:btih:1f739d935676111cfff4b4693e3816e664797050&dn=gpl-3.0.txt GPL-v3-or-Later

		var params = new URLSearchParams(location.search);
		var r      = params.get("r");
		if (r)
			document.write("<a class='alert_right button' href='" + r + "'>Okay</a>");
		else
			$("#warning").hide();
	</script>
</div>

The use of WTFPL as a license is discouraged for multiple reasons.

* **No Warranty disclaimer:** This could open you up to being sued.<sup>[1]</sup>
* **Swearing:** This prevents settings like schools from using your content.
* **Not OSI Approved:** Same as public domain?

The Open Source Initiative chose not to approve the license as an open-source
license, saying:<sup>[3]</sup>

> It's no different from dedication to the public domain.
> Author has submitted license approval request – author is free to make public domain dedication.
> Although he agrees with the recommendation, Mr. Michlmayr notes that public domain doesn't exist in Europe. Recommend: Reject.

## Sources

1. [WTFPL is harmful to software developers](https://cubicspot.blogspot.com/2017/04/wtfpl-is-harmful-to-software-developers.html)
2. [FSF](https://www.gnu.org/licenses/license-list.en.html)
3. [OSI](https://opensource.org/minutes20090304)
