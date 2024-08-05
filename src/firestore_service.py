import firebase_admin
from firebase_admin import credentials, firestore
import os
import logging
from google.cloud import firestore
from google.api_core import retry
from datetime import datetime

class FirestoreService:
    def __init__(self, credentials_path=None):
        if credentials_path is None:
            credentials_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

        if not credentials_path or not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Firebase credentials file not found at: {credentials_path}")

        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred)

        self.db = firestore.Client()
        self.last_update_time = firestore.SERVER_TIMESTAMP
        logging.info("FirestoreService initialized successfully")

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
    def get_companies(self, collection, festival=None):
        logging.info(f"Fetching companies from collection: {collection}, festival: {festival}")
        try:
            query = self.db.collection(collection)
            if festival and festival != "All Festivals":
                query = query.where('ProgramName', '==', festival)

            companies = list(query.get())

            result = []
            for company in companies:
                try:
                    company_data = company.to_dict()
                    company_data['Id'] = company.id
                    sn_count = self.get_sn_count(collection, company.id)
                    company_data['sn_count'] = sn_count
                    result.append(company_data)
                except Exception as e:
                    logging.error(f"Error processing company document {company.id}: {e}", exc_info=True)

            logging.info(f"Successfully processed {len(result)} companies")
            return result
        except Exception as e:
            logging.error(f"Error fetching companies: {e}", exc_info=True)
            raise

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
            festivals = self.db.collection('Programs').get()
            return [festival.to_dict().get('ProgramName', 'Unknown Festival') for festival in festivals]
        except Exception as e:
            logging.error(f"Error fetching festivals: {e}")
            return []

    def generate_id(self):
        return self.db.collection('dummy').document().id

    def get_company_updates(self, collection, last_update_time):
        try:
            updates = self.db.collection(collection).where('LastModified', '>', last_update_time).get()
            return [{**doc.to_dict(), 'Id': doc.id} for doc in updates]
        except Exception as e:
            logging.error(f"Error fetching company updates: {e}")
            raise

    def get_companies_paginated(self, collection, start, end):
        try:
            query = self.db.collection(collection).order_by('CreatedAt').offset(start).limit(end - start)
            docs = query.get()
            return [{**doc.to_dict(), 'Id': doc.id} for doc in docs]
        except Exception as e:
            logging.error(f"Error fetching paginated companies: {e}")
            raise

    @property
    def server_timestamp(self):
        return firestore.SERVER_TIMESTAMP