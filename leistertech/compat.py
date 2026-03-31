import frappe


def apply_v16_patches():
	"""Apply small runtime patches needed for the v16 migration."""
	from frappe.utils.user import UserPermissions

	if getattr(UserPermissions, "_leistertech_v16_patched", False):
		return

	def setup_user(self):
		def get_user_doc():
			user = None
			try:
				# Exclude virtual child tables from the cached user doc.
				# This avoids v16 boot failures when a computed table serializes
				# into plain dicts before desk boot completes.
				user = frappe.get_doc("User", self.name).as_dict(ignore_computed_child_tables=True)
			except frappe.DoesNotExistError:
				pass
			except Exception as e:
				if not frappe.db.is_table_missing(e):
					raise

			return user

		if not frappe.flags.in_install_db and not frappe.in_test:
			user_doc = frappe.cache.hget("user_doc", self.name, get_user_doc)
			if user_doc:
				self.doc = frappe.get_doc(user_doc)

	UserPermissions.setup_user = setup_user
	UserPermissions._leistertech_v16_patched = True
