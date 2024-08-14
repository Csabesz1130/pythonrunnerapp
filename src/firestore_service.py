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
                self.db = firestore.Client.from_service_account_json(credentials_path)
            else:
                self.db = firestore.Client()
            logging.info("Firestore client initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize Firestore client: {e}")
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
    def get_companies_paginated(self, festival, start, end):
        try:
            logging.info(f"Fetching companies for festival: {festival}, start: {start}, end: {end}")
            query = self.db.collection('Company_Install').where('ProgramName', '==', festival)
            query = query.order_by('CompanyName').offset(start).limit(end - start)
            companies = query.get()
            result = [{**doc.to_dict(), 'Id': doc.id} for doc in companies]
            logging.info(f"Retrieved {len(result)} companies")
            return result
        except Exception as e:
            logging.error(f"Error fetching paginated companies: {e}", exc_info=True)
            raise

    @retry.Retry(predicate=retry.if_exception_type(Exception))
    def get_total_companies(self, festival):
        try:
            logging.info(f"Getting total companies for festival: {festival}")
            query = self.db.collection('Company_Install').where('ProgramName', '==', festival)
            total = len(query.get())
            logging.info(f"Total companies: {total}")
            return total
        except Exception as e:
            logging.error(f"Error getting total companies: {e}", exc_info=True)
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