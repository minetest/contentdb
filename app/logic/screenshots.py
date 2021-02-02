from werkzeug.exceptions import abort

from app.logic.uploads import upload_file
from app.models import User, Package, PackageScreenshot, Permission, NotificationType, db
from app.utils import addNotification


def do_create_screenshot(user: User, package: Package, title: str, file):
	uploaded_url, uploaded_path = upload_file(file, "image", "a PNG or JPG image file")

	counter = 1
	for screenshot in package.screenshots:
		screenshot.order = counter
		counter += 1

	ss = PackageScreenshot()
	ss.package  = package
	ss.title    = title or "Untitled"
	ss.url      = uploaded_url
	ss.approved = package.checkPerm(user, Permission.APPROVE_SCREENSHOT)
	ss.order    = counter
	db.session.add(ss)

	msg = "Screenshot added {}" \
			.format(ss.title)
	addNotification(package.maintainers, user, NotificationType.PACKAGE_EDIT, msg, package.getDetailsURL(), package)
	db.session.commit()

	return ss
