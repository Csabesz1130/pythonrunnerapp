import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging

class FirestoreService:
    def __init__(self, credentials_path=None):
        if credentials_path is None:
            credentials_path = r"C:\Users\Balogh Csaba\IdeaProjects\pythonrunnerapp\resources\runnerapp-232cc-firebase-adminsdk-2csiq-7074e046ed.json"

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
            return companies_ref.get()
        except Exception as e:
            logging.error(f"Error fetching companies: {e}")
            return []

    def get_company(self, collection, company_id):
        try:
            return self.db.collection(collection).document(company_id).get().to_dict()
        except Exception as e:
            logging.error(f"Error fetching company details: {e}")
            return {}

    # ... (other methods remain the same)

    def add_company(self, collection, data):
        return self.db.collection(collection).add(data)[1].id

    def update_company(self, collection, company_id, data):
        self.db.collection(collection).document(company_id).update(data)

    def delete_company(self, collection, company_id):
        self.db.collection(collection).document(company_id).delete()

    def add_comment(self, collection, company_id, comment_data):
        company_ref = self.db.collection(collection).document(company_id)
        company_ref.update({
            "comments": firestore.ArrayUnion([comment_data])
        })

    def server_timestamp(self):
        return firestore.SERVER_TIMESTAMP