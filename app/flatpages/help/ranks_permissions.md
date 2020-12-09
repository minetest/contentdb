title: Ranks and Permissions

## Overview

* **New Members** - mostly untrusted, cannot change package meta data or publish releases without approval.
* **Members** - Trusted to change the meta data of their own packages', but cannot approve their own packages.
* **Trusted Members** - Same as above, but can approve their own releases.
* **Editors** - Trusted to edit any package or release, and also responsible for approving new packages.
* **Moderators** - Same as above, but can manage users.
* **Admins** - Full access.

## Breakdown

<table class="table table-striped ranks-table">
	<thead>
		<tr>
			<th>Rank</th>
			<th colspan=2 class="NEW_MEMBER">New Member</th>
			<th colspan=2 class="MEMBER">Member</th>
			<th colspan=2 class="TRUSTED_MEMBER">Trusted</th>
			<th colspan=2 class="EDITOR">Editor</th>
			<th colspan=2 class="MODERATOR">Moderator</th>
			<th colspan=2 class="ADMIN">Admin</th>
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
			<td>✓</td> <!-- new -->
			<td></td>
			<td>✓</td> <!-- member -->
			<td></td>
			<td>✓</td> <!-- trusted member -->
			<td></td>
			<td>✓</td> <!-- editor -->
			<td>✓</td>
			<td>✓</td> <!-- moderator -->
			<td>✓</td>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
		<tr>
			<td>Approve Package</td>
			<td></td> <!-- new -->
			<td></td>
			<td></td> <!-- member -->
			<td></td>
			<td></td> <!-- trusted member -->
			<td></td>
			<td>✓</td> <!-- editor -->
			<td>✓</td>
			<td>✓</td> <!-- moderator -->
			<td>✓</td>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
		<tr>
			<td>Delete Package</td>
			<td></td> <!-- new -->
			<td></td>
			<td>✓</td> <!-- member -->
			<td></td>
			<td>✓</td> <!-- trusted member -->
			<td></td>
			<td>✓</td> <!-- editor -->
			<td>✓</td>
			<td>✓</td> <!-- moderator -->
			<td>✓</td>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
		<tr>
			<td>Edit Package</td>
			<td></td> <!-- new -->
			<td></td>
			<td>✓</td> <!-- member -->
			<td></td>
			<td>✓</td> <!-- trusted member -->
			<td></td>
			<td>✓</td> <!-- editor -->
			<td>✓</td>
			<td>✓</td> <!-- moderator -->
			<td>✓</td>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
		<tr>
			<td>Edit Maintainers</td>
			<td>✓</td> <!-- new -->
			<td></td>
			<td>✓</td> <!-- member -->
			<td></td>
			<td>✓</td> <!-- trusted member -->
			<td></td>
			<td>✓</td> <!-- editor -->
			<td></td>
			<td>✓</td> <!-- moderator -->
			<td>✓</td>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
		<tr>
			<td>Add/Delete Screenshot</td>
			<td>✓</td> <!-- new -->
			<td></td>
			<td>✓</td> <!-- member -->
			<td></td>
			<td>✓</td> <!-- trusted member -->
			<td></td>
			<td>✓</td> <!-- editor -->
			<td>✓</td>
			<td>✓</td> <!-- moderator -->
			<td>✓</td>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
		<tr>
			<td>Approve Screenshot</td>
			<td></td> <!-- new -->
			<td></td>
			<td></td> <!-- member -->
			<td></td>
			<td>✓</td> <!-- trusted member -->
			<td></td>
			<td>✓</td> <!-- editor -->
			<td>✓</td>
			<td>✓</td> <!-- moderator -->
			<td>✓</td>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
		<tr>
			<td>Make Release</td>
			<td>✓</td> <!-- new -->
			<td></td>
			<td>✓</td> <!-- member -->
			<td></td>
			<td>✓</td> <!-- trusted member -->
			<td></td>
			<td>✓</td> <!-- editor -->
			<td>✓</td>
			<td>✓</td> <!-- moderator -->
			<td>✓</td>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
		<tr>
			<td>Approve Release</td>
			<td></td> <!-- new -->
			<td></td>
			<td>✓</td> <!-- member -->
			<td></td>
			<td>✓</td> <!-- trusted member -->
			<td></td>
			<td>✓</td> <!-- editor -->
			<td>✓</td>
			<td>✓</td> <!-- moderator -->
			<td>✓</td>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
		<tr>
			<td>Change Release URL</td>
			<td></td> <!-- new -->
			<td></td>
			<td></td> <!-- member -->
			<td></td>
			<td></td> <!-- trusted member -->
			<td></td>
			<td></td> <!-- editor -->
			<td></td>
			<td></td> <!-- moderator -->
			<td></td>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
		<tr>
			<td>See Private Thread</td>
			<td>✓</td> <!-- new -->
			<td></td>
			<td>✓</td> <!-- member -->
			<td></td>
			<td>✓</td> <!-- trusted member -->
			<td></td>
			<td>✓</td> <!-- editor -->
			<td>✓</td>
			<td>✓</td> <!-- moderator -->
			<td>✓</td>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
		<tr>
			<td>Edit Comments</td>
			<td></td> <!-- new -->
			<td></td>
			<td>✓</td> <!-- member -->
			<td></td>
			<td>✓</td> <!-- trusted member -->
			<td></td>
			<td>✓</td> <!-- editor -->
			<td></td>
			<td>✓</td> <!-- moderator -->
			<td></td>
			<td>✓</td> <!-- admin -->
			<td></td>
		</tr>
		<tr>
			<td>Set Email</td>
			<td>✓</td> <!-- new -->
			<td></td>
			<td>✓</td> <!-- member -->
			<td></td>
			<td>✓</td> <!-- trusted member -->
			<td></td>
			<td>✓</td> <!-- editor -->
			<td></td>
			<td>✓</td> <!-- moderator -->
			<th>✓<sup>2</sup></th>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
		<tr>
			<td>Create Token</td>
			<td></td> <!-- new -->
			<td></td>
			<td>✓</td> <!-- member -->
			<td></td>
			<td>✓</td> <!-- trusted member -->
			<td></td>
			<td>✓</td> <!-- editor -->
			<td></td>
			<td>✓</td> <!-- moderator -->
			<th>✓<sup>2</sup></th>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
		<tr>
			<td>Set Rank</td>
			<td></td> <!-- new -->
			<td></td>
			<td></td> <!-- member -->
			<td></td>
			<td></td> <!-- trusted member -->
			<td></td>
			<td></td> <!-- editor -->
			<td></td>
			<th>✓<sup>3</sup></th> <!-- moderator -->
			<th>✓<sup>2</sup><sup>3</sup></th>
			<td>✓</td> <!-- admin -->
			<td>✓</td>
		</tr>
	</tbody>
</table>


2. Target user cannot be an admin.
3. Cannot set user to a higher rank than themselves.
