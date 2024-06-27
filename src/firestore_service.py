import time

import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging

from google.cloud.exceptions import NotFound


class FirestoreService:
    def __init__(self, credentials_path=None):
        if credentials_path is None:
            credentials_path = r"C:\Users\Balogh Csaba\IdeaProjects\pythonrunnerapp\resources\runnerapp-232cc-firebase-adminsdk-2csiq-a27b27e8c7.json"

        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Firebase credentials file not found at: {credentials_path}")

        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)
        self.db = firestore.client()

    def get_festivals(self):
        try:
            festivals = self.db.collection('Programs').get()
            return [festival.to_dict().get('ProgramName', 'Unknown Festival') for festival in festivals]
        except Exception as e:
            logging.error(f"Error fetching festivals: {e}")
            return []

    def get_companies(self, collection, festival=None):
        try:
            companies_ref = self.db.collection(collection)
            if festival and festival != "All Festivals":
                companies_ref = companies_ref.where('ProgramName', '==', festival)

            companies = companies_ref.get()

            if not companies:
                logging.warning(f"No companies found in collection: {collection}, festival: {festival}")
                return []

            return [company.to_dict() for company in companies]
        except NotFound:
            logging.error(f"Collection not found: {collection}")
            return []
        except Exception as e:
            logging.error(f"Error fetching companies: {e}", exc_info=True)
            return []

    def get_company(self, collection, company_id):
        try:
            return self.db.collection(collection).document(company_id).get().to_dict()
        except Exception as e:
            logging.error(f"Error fetching company details: {e}")
            return {}

    def generate_id(self):
        # Generate a unique ID based on the current timestamp
        return str(int(time.time() * 1000))

    def add_company(self, collection, data):
        return self.db.collection(collection).add(data)[1].id

    def update_company(self, collection, company_id, data):
        doc_ref = self.db.collection(collection).document(company_id)
        doc = doc_ref.get()
        if doc.exists:
            doc_ref.update(data)
        else:
            raise ValueError(f"No document found with ID: {company_id} in collection: {collection}")

    def delete_company(self, collection, company_id):
        self.db.collection(collection).document(company_id).delete()

    def add_comment(self, collection, company_id, comment_data):
        company_ref = self.db.collection(collection).document(company_id)
        company_ref.update({
            "comments": firestore.ArrayUnion([comment_data])
        })

    def server_timestamp(self):
        return firestore.SERVER_TIMESTAMP