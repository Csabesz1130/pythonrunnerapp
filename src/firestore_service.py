import bcrypt
import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging
from google.cloud import firestore
from google.api_core import retry
from datetime import datetime

class FirestoreService:
    def __init__(self, credentials_path=None):
        try:
            if credentials_path:
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred)
                logging.info(f"Initialized Firebase app with credentials from {credentials_path}")
            else:
                firebase_admin.initialize_app()
                logging.info("Initialized Firebase app with default credentials")
            self.db = firestore.Client()
            logging.info("Firestore client initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Firestore client: {e}", exc_info=True)
            raise ValueError(f"Failed to initialize Firestore client. Error: {str(e)}")

    def get_all_documents(self, collection):
        try:
            docs = self.db.collection(collection).get()
            return [{
                **doc.to_dict(),
                'Id': doc.id,
                'CreatedAt': doc.create_time.strftime("%Y-%m-%d %H:%M:%S") if doc.create_time else None,
            } for doc in docs]
        except Exception as e:
            logging.error(f"Error fetching documents from {collection}: {e}")
            raise

    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def get_total_companies(self, festival, collection):
        try:
            logging.info(f"Getting total companies for festival: {festival} in collection: {collection}")
            query = self.db.collection(collection).where('ProgramName', '==', festival)
            total = len(query.get())
            logging.info(f"Total companies: {total}")
            return total
        except Exception as e:
            logging.error(f"Error getting total companies: {e}", exc_info=True)
            raise

    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def get_companies_paginated(self, festival, collection, start, end):
        try:
            logging.info(f"Fetching companies for festival: {festival}, collection: {collection}, start: {start}, end: {end}")
            query = self.db.collection(collection).where('ProgramName', '==', festival)
            query = query.order_by('CompanyName').offset(start).limit(end - start)
            companies = query.get()
            result = [{**doc.to_dict(), 'Id': doc.id} for doc in companies]
            logging.info(f"Retrieved {len(result)} companies")
            return result
        except Exception as e:
            logging.error(f"Error fetching paginated companies: {e}", exc_info=True)
            raise

    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def get_company_details(self, company_id):
        try:
            logging.info(f"Fetching details for company: {company_id}")
            doc_ref = self.db.collection('Company_Install').document(company_id)
            doc = doc_ref.get()
            if not doc.exists:
                logging.warning(f"Company {company_id} not found")
                return None
            company_data = doc.to_dict()
            company_data['Id'] = doc.id

            # Fetch SN numbers
            sn_collection = doc_ref.collection('SN')
            sn_docs = sn_collection.get()
            company_data['SN'] = [sn_doc.get('SN') for sn_doc in sn_docs if sn_doc.get('SN')]

            # Fetch Comments
            comments_collection = doc_ref.collection('Comments')
            comment_docs = comments_collection.order_by('Timestamp', direction=firestore.Query.DESCENDING).get()
            company_data['Comments'] = [{
                'comment': comment_doc.get('Comment'),
                'timestamp': comment_doc.get('Timestamp')
            } for comment_doc in comment_docs if comment_doc.get('Comment') and comment_doc.get('Timestamp')]

            return company_data
        except Exception as e:
            logging.error(f"Error fetching company details: {e}", exc_info=True)
            raise

    def get_all_users(self):
        try:
            users = self.db.collection('users').get()
            return [{'username': user.get('username'), 'role': user.get('role')} for user in users]
        except Exception as e:
            logging.error(f"Error getting users: {e}")
            raise

    def add_user(self, username, password, role='superuser'):
        try:
            users_ref = self.db.collection('users')
            logging.info(f"Checking if user {username} already exists")
            existing_user = users_ref.where('username', '==', username).get()
            if existing_user:
                logging.warning(f"User already exists: {username}")
                return False, "User already exists"

            logging.info(f"Adding new user: {username}")
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            new_user = {
                'username': username,
                'password_hash': password_hash.decode('utf-8'),
                'role': role
            }
            users_ref.add(new_user)
            logging.info(f"User added successfully: {username}")
            return True, "User added successfully"
        except Exception as e:
            logging.error(f"Error adding user {username}: {e}", exc_info=True)
            return False, str(e)

    def get_user(self, username):
        try:
            logging.info(f"Attempting to get user: {username}")
            users_ref = self.db.collection('users')
            user_docs = users_ref.where('username', '==', username).get()
            if user_docs:
                user_doc = user_docs[0]
                user_data = user_doc.to_dict()
                logging.info(f"User found: {username}")
                return {
                    'id': user_doc.id,
                    'username': user_data['username'],
                    'role': user_data.get('role', 'user')
                }
            logging.warning(f"User not found: {username}")
            return None
        except Exception as e:
            logging.error(f"Error getting user {username}: {e}", exc_info=True)
            return None

    def authenticate_user(self, username, password):
        # Hardcoded users
        users = {
            "csaba": {"password": "1234576", "role": "superuser"},
            "hds": {"password": "1234567", "role": "superuser"}
        }

        if username in users and users[username]["password"] == password:
            logging.info(f"User authenticated: {username}")
            return {
                "username": username,
                "role": users[username]["role"]
            }
        else:
            logging.warning(f"Authentication failed for user: {username}")
            return None

    def delete_user(self, username):
        try:
            user_query = self.db.collection('users').where('username', '==', username).limit(1).get()
            if not user_query:
                return False, "User not found"

            user_doc = user_query[0]
            user_doc.reference.delete()
            return True, "User deleted successfully"
        except Exception as e:
            logging.error(f"Error deleting user: {e}")
            return False, str(e)

    def get_sn_numbers(self, company_id):
        try:
            sn_collection = self.db.collection('Company_Install').document(company_id).collection('SN')
            sn_docs = sn_collection.get()
            return [doc.get('SN') for doc in sn_docs if doc.get('SN')]
        except Exception as e:
            logging.error(f"Error fetching SN numbers for company {company_id}: {e}", exc_info=True)
            return []

    def get_company(self, collection, company_id):
        try:
            doc_ref = self.db.collection(collection).document(company_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                data['Id'] = doc.id
                return data
            else:
                logging.warning(f"No company found with ID: {company_id} in collection: {collection}")
                return None
        except Exception as e:
            logging.error(f"Error fetching company {company_id} from {collection}: {e}")
            raise

    def add_company(self, collection, data):
        try:
            doc_ref = self.db.collection(collection).document()
            sn_list = data.pop('SN', [])
            data['LastModified'] = firestore.SERVER_TIMESTAMP
            data['CreatedAt'] = firestore.SERVER_TIMESTAMP
            doc_ref.set(data)

            for sn in sn_list:
                doc_ref.collection('SN').add({'SN': sn})

            return doc_ref.id
        except Exception as e:
            logging.error(f"Error adding company to {collection}: {e}")
            raise

    def update_company(self, collection, company_id, data):
        try:
            doc_ref = self.db.collection(collection).document(company_id)
            sn_list = data.pop('SN', None)
            data['LastModified'] = firestore.SERVER_TIMESTAMP
            doc_ref.update(data)

            if sn_list is not None:
                self.update_sn_list(company_id, sn_list)

            return True
        except Exception as e:
            logging.error(f"Error updating company {company_id} in {collection}: {e}")
            raise

    def delete_company(self, collection, company_id):
        try:
            self.db.collection(collection).document(company_id).delete()
        except Exception as e:
            logging.error(f"Error deleting company {company_id} from {collection}: {e}")
            raise

    def get_sn_count(self, collection, company_id):
        try:
            sn_collection = self.db.collection(collection).document(company_id).collection('SN')
            return len(sn_collection.get())
        except Exception as e:
            logging.error(f"Error getting SN count for company {company_id}: {e}")
            return 0

    def get_sn_list(self, company_id):
        try:
            sn_collection = self.db.collection("Company_Install").document(company_id).collection('SN')
            sn_docs = sn_collection.get()
            return [doc.to_dict()['SN'] for doc in sn_docs if 'SN' in doc.to_dict()]
        except Exception as e:
            logging.error(f"Error fetching SN list for company {company_id}: {e}")
            raise

    def update_sn_list(self, company_id, sn_list):
        try:
            sn_collection = self.db.collection("Company_Install").document(company_id).collection('SN')
            batch = self.db.batch()

            # Delete existing SN documents
            existing_docs = sn_collection.get()
            for doc in existing_docs:
                batch.delete(doc.reference)

            # Add new SN documents
            for sn in sn_list:
                new_doc_ref = sn_collection.document()
                batch.set(new_doc_ref, {'SN': sn})

            batch.commit()
        except Exception as e:
            logging.error(f"Error updating SN list for company {company_id}: {e}")
            raise

    def get_festivals(self):
        try:
            logging.info("Fetching festivals")
            festivals = self.db.collection('Programs').get()
            result = [festival.to_dict().get('ProgramName', 'Unknown Festival') for festival in festivals]
            logging.info(f"Retrieved {len(result)} festivals")
            return result
        except Exception as e:
            logging.error(f"Error fetching festivals: {e}", exc_info=True)
            return []

    def generate_id(self):
        return self.db.collection('dummy').document().id

    def get_companies(self, collection, festival):
        try:
            companies = self.db.collection(collection).where('ProgramName', '==', festival).get()
            return [{**doc.to_dict(), 'Id': doc.id} for doc in companies]
        except Exception as e:
            logging.error(f"Error fetching companies from {collection}: {e}", exc_info=True)
            raise

    def update_or_create_company(self, collection, company_data):
        try:
            company_id = company_data['Id']
            doc_ref = self.db.collection(collection).document(company_id)

            # Check if the document exists
            doc = doc_ref.get()
            if doc.exists:
                # Update existing document
                doc_ref.update(company_data)
                logging.info(f"Updated existing company with ID: {company_id}")
            else:
                # Create new document
                doc_ref.set(company_data)
                logging.info(f"Created new company with ID: {company_id}")

            return True
        except Exception as e:
            logging.error(f"Error updating or creating company: {e}", exc_info=True)
            raise

    def get_company_updates(self, collection, last_update_time):
        try:
            updates = self.db.collection(collection).where('LastModified', '>', last_update_time).get()
            return [{**doc.to_dict(), 'Id': doc.id} for doc in updates]
        except Exception as e:
            logging.error(f"Error fetching company updates: {e}")
            raise

    @property
    def server_timestamp(self):
        return firestore.SERVER_TIMESTAMP