import os
from google.cloud import firestore
import time
import logging

class FirestoreService:
    def __init__(self, credentials_path=None):
        try:
            if credentials_path:
                self.db = firestore.Client.from_service_account_json(credentials_path)
            else:
                # If no path is provided, try to use the environment variable
                self.db = firestore.Client()
            logging.info("Firestore client initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Firestore client: {e}")
            raise ValueError(f"Failed to initialize Firestore client. Error: {str(e)}")

    def get_all_documents(self, collection):
        try:
            docs = self.db.collection(collection).get()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logging.error(f"Error fetching documents from {collection}: {e}")
            raise

    def get_company(self, collection, company_id):
        try:
            doc = self.db.collection(collection).document(company_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logging.error(f"Error fetching company {company_id} from {collection}: {e}")
            raise

    def add_company(self, collection, data):
        try:
            doc_ref = self.db.collection(collection).document()
            doc_ref.set(data)
            return doc_ref.id
        except Exception as e:
            logging.error(f"Error adding company to {collection}: {e}")
            raise

    def get_all_documents(self, collection):
        try:
            docs = self.db.collection(collection).get()
            return [{
                **doc.to_dict(),
                'Id': doc.id,
                'CreatedAt': doc.create_time.strftime("%Y-%m-%d %H:%M:%S") if doc.create_time else None,
                # Ensure boolean fields are properly retrieved
                'Elosztó': doc.get('Elosztó', False),
                '3': doc.get('3', False),  # Assuming '3' is the Elosztó field
                '4': doc.get('4', False),  # Áram
                '5': doc.get('5', False),  # Hálózat
                '6': doc.get('6', False),  # PTG
                '7': doc.get('7', False),  # Szoftver
                '8': doc.get('8', False),  # Param
                '9': doc.get('9', False),  # Helyszín
            } for doc in docs]
        except Exception as e:
            logging.error(f"Error fetching documents from {collection}: {e}")
            raise

    def update_company(self, collection, company_id, data):
        try:
            doc_ref = self.db.collection(collection).document(company_id)
            doc_ref.update(data)
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

    def generate_id(self):
        return str(int(time.time() * 1000))

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