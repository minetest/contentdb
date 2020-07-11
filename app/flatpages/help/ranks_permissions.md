title: Ranks and Permissions

## Overview

* **New Members** - mostly untrusted, cannot change package meta data or publish releases without approval.
* **Members** - Trusted to change the meta data of their own packages', but cannot publish releases.
* **Trusted Members** - Same as above, but can approve their own releases and packages.
* **Editors** - Trusted to change the meta data of any package, and also make and publish releases.
* **Moderators** - Same as above, but can manage users.
* **Admins** - Full access.

## Breakdown

<table class="table">
	<thead>
		<tr>
			<th>Rank</th>
			<th colspan=2>New Member</th>
			<th colspan=2>Member</th>
			<th colspan=2>Trusted Member</th>
			<th colspan=2>Editor</th>
			<th colspan=2>Moderator</th>
			<th colspan=2>Admin</th>
		</tr>
		<tr>
			<th>Owner of thing</th>
			<th>Y</th>
			<th>N</th>
			<th>Y</th>
			<th>N</th>
			<th>Y</th>
			<th>N</th>
			<th>Y</th>
			<th>N</th>
			<th>Y</th>
			<th>N</th>
			<th>Y</th>
			<th>N</th>
		</tr>
	</thead>
	<tbody>
		<tr>
			<td>Create Package</td>
			<th>✓</th> <!-- new -->
			<th></th>
			<th>✓</th> <!-- member -->
			<th></th>
			<th>✓</th> <!-- trusted member -->
			<th></th>
			<th>✓</th> <!-- editor -->
			<th>✓</th>
			<th>✓</th> <!-- moderator -->
			<th>✓</th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>Approve Package</td>
			<th></th> <!-- new -->
			<th></th>
			<th></th> <!-- member -->
			<th></th>
			<th></th> <!-- trusted member -->
			<th></th>
			<th>✓</th> <!-- editor -->
			<th>✓</th>
			<th>✓</th> <!-- moderator -->
			<th>✓</th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>Delete Package</td>
			<th></th> <!-- new -->
			<th></th>
			<th></th> <!-- member -->
			<th></th>
			<th></th> <!-- trusted member -->
			<th></th>
			<th>✓</th> <!-- editor -->
			<th>✓</th>
			<th>✓</th> <!-- moderator -->
			<th>✓</th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>Edit Package</td>
			<th></th> <!-- new -->
			<th></th>
			<th>✓</th> <!-- member -->
			<th></th>
			<th>✓</th> <!-- trusted member -->
			<th></th>
			<th>✓</th> <!-- editor -->
			<th>✓</th>
			<th>✓</th> <!-- moderator -->
			<th>✓</th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>Edit Maintainers</td>
			<th>✓</th> <!-- new -->
			<th></th>
			<th>✓</th> <!-- member -->
			<th></th>
			<th>✓</th> <!-- trusted member -->
			<th></th>
			<th>✓</th> <!-- editor -->
			<th></th>
			<th>✓</th> <!-- moderator -->
			<th>✓</th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>Add/Delete Screenshot</td>
			<th>✓</th> <!-- new -->
			<th></th>
			<th>✓</th> <!-- member -->
			<th></th>
			<th>✓</th> <!-- trusted member -->
			<th></th>
			<th>✓</th> <!-- editor -->
			<th>✓</th>
			<th>✓</th> <!-- moderator -->
			<th>✓</th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>Approve Screenshot</td>
			<th></th> <!-- new -->
			<th></th>
			<th></th> <!-- member -->
			<th></th>
			<th>✓</th> <!-- trusted member -->
			<th></th>
			<th>✓</th> <!-- editor -->
			<th>✓</th>
			<th>✓</th> <!-- moderator -->
			<th>✓</th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>Make Release</td>
			<th>✓</th> <!-- new -->
			<th></th>
			<th>✓</th> <!-- member -->
			<th></th>
			<th>✓</th> <!-- trusted member -->
			<th></th>
			<th>✓</th> <!-- editor -->
			<th>✓</th>
			<th>✓</th> <!-- moderator -->
			<th>✓</th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>Approve Release</td>
			<th></th> <!-- new -->
			<th></th>
			<th></th> <!-- member -->
			<th></th>
			<th>✓</th> <!-- trusted member -->
			<th></th>
			<th>✓</th> <!-- editor -->
			<th>✓</th>
			<th>✓</th> <!-- moderator -->
			<th>✓</th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>Change Release URL</td>
			<th></th> <!-- new -->
			<th></th>
			<th></th> <!-- member -->
			<th></th>
			<th></th> <!-- trusted member -->
			<th></th>
			<th></th> <!-- editor -->
			<th></th>
			<th></th> <!-- moderator -->
			<th></th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>See Private Thread</td>
			<th>✓</th> <!-- new -->
			<th></th>
			<th>✓</th> <!-- member -->
			<th></th>
			<th>✓</th> <!-- trusted member -->
			<th></th>
			<th>✓</th> <!-- editor -->
			<th>✓</th>
			<th>✓</th> <!-- moderator -->
			<th>✓</th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>Edit Comments</td>
			<th>✓</th> <!-- new -->
			<th></th>
			<th>✓</th> <!-- member -->
			<th></th>
			<th>✓</th> <!-- trusted member -->
			<th></th>
			<th>✓</th> <!-- editor -->
			<th></th>
			<th>✓</th> <!-- moderator -->
			<th></th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>Set Email</td>
			<th>✓</th> <!-- new -->
			<th></th>
			<th>✓</th> <!-- member -->
			<th></th>
			<th>✓</th> <!-- trusted member -->
			<th></th>
			<th>✓</th> <!-- editor -->
			<th></th>
			<th>✓</th> <!-- moderator -->
			<th>✓<sup>2</sup></th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>Create Token</td>
			<th></th> <!-- new -->
			<th></th>
			<th>✓</th> <!-- member -->
			<th></th>
			<th>✓</th> <!-- trusted member -->
			<th></th>
			<th>✓</th> <!-- editor -->
			<th></th>
			<th>✓</th> <!-- moderator -->
			<th>✓<sup>2</sup></th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
		<tr>
			<td>Set Rank</td>
			<th></th> <!-- new -->
			<th></th>
			<th></th> <!-- member -->
			<th></th>
			<th></th> <!-- trusted member -->
			<th></th>
			<th></th> <!-- editor -->
			<th></th>
			<th>✓<sup>3</sup></th> <!-- moderator -->
			<th>✓<sup>2</sup><sup>3</sup></th>
			<th>✓</th> <!-- admin -->
			<th>✓</th>
		</tr>
	</tbody>
</table>


1. User must be the author of the EditRequest.
2. Target user cannot be an admin.
3. Cannot set user to a higher rank than themselves.
