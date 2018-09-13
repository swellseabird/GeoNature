from sqlalchemy import ForeignKey, or_
from sqlalchemy.orm import relationship
from sqlalchemy.sql import select, func
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry

from werkzeug.exceptions import NotFound

from pypnnomenclature.models import TNomenclatures

from geonature.utils.utilssqlalchemy import (
    serializable, geoserializable
)
from geonature.utils.utilsgeometry import shapeserializable
from geonature.utils.env import DB
from geonature.core.gn_meta.models import TDatasets, TAcquisitionFramework
from geonature.core.ref_geo.models import LAreas
from geonature.core.ref_geo.models import LiMunicipalities
from pypnusershub.db.tools import InsufficientRightsError


class SyntheseCruved(DB.Model):
    """
        Abstract class to add method
        to control the data access according
        to the user rights
    """
    __abstract__ = True

    def user_is_observer(self, user):
        # faire la vérification sur le champs observateur ?
        cor_observers = [d.id_role for d in self.cor_observers]
        # return user.id_role == self.id_digitiser or user.id_role in observers
        return user.id_role in cor_observers

    def user_is_in_dataset_actor(self, user_datasets):
        return self.id_dataset in user_datasets

    def user_is_allowed_to(self, user, level, user_datasets):
        """
            Function to know if a user can do action
            on a data
        """
        # Si l'utilisateur n'a pas de droit d'accès aux données

        if level not in ('1', '2', '3'):
            return False

        # Si l'utilisateur à le droit d'accéder à toutes les données
        if level == '3':
            return True

        # Si l'utilisateur est propriétaire de la données
        if self.user_is_observer(user):
            return True

        # Si l'utilisateur appartient à un organisme
        # qui a un droit sur la données et
        # que son niveau d'accès est 2 ou 3
        if (
            self.user_is_in_dataset_actor(user_datasets) and
            level in ('2', '3')
        ):
            return True
        return False

    def get_observation_if_allowed(self, user, user_datasets):
        """
            Return the observation if the user is allowed
            params:
                user: object from TRole
        """
        if self.user_is_allowed_to(user, user.tag_object_code, user_datasets):
            return self

        raise InsufficientRightsError(
            ('User "{}" cannot "{}" this current releve')
            .format(user.id_role, user.tag_action_code),
            403
        )

    def get_synthese_cruved(self, user, user_cruved, users_datasets):
        """
        Return the user's cruved for a Synthese instance.
        Use in the map-list interface to allow or not an action
        params:
            - user : a TRole object
            - user_cruved: object return by cruved_for_user_in_app(user)
            - users_dataset: array of dataset ids where the users have rights
        """
        return {
            action: self.user_is_allowed_to(user, level, users_datasets)
            for action, level in user_cruved.items()
        }


@serializable
class TSources(DB.Model):
    __tablename__ = 't_sources'
    __table_args__ = {'schema': 'gn_synthese'}
    id_source = DB.Column(DB.Integer, primary_key=True)
    name_source = DB.Column(DB.Unicode)
    desc_source = DB.Column(DB.Unicode)
    entity_source_pk_field = DB.Column(DB.Unicode)
    url_source = DB.Column(DB.Unicode)
    target = DB.Column(DB.Unicode)
    picto_source = DB.Column(DB.Unicode)
    groupe_source = DB.Column(DB.Unicode)
    active = DB.Column(DB.Boolean)
    meta_create_date = DB.Column(DB.DateTime)
    meta_update_date = DB.Column(DB.DateTime)


@serializable
class CorRoleSynthese(DB.Model):
    __tablename__ = 'cor_role_synthese'
    __table_args__ = {'schema': 'gn_synthese'}
    id_synthese = DB.Column(DB.Integer, ForeignKey('gn_synthese.synthese.id_synthese'), primary_key=True)
    id_role = DB.Column(DB.Integer, ForeignKey('utilisateurs.t_roles.id_role'), primary_key=True)


corAreaSynthese = DB.Table(
    'cor_area_synthese',
    DB.MetaData(schema='gn_synthese'),
    DB.Column(
        'id_synthese',
        DB.Integer,
        ForeignKey('gn_synthese.cor_area_synthese.id_synthese'),
        primary_key=True
    ),
    DB.Column(
        'id_area',
        DB.Integer,
        ForeignKey('ref_geo.t_areas.id_area'),
        primary_key=True
    )
)


@serializable
class VSyntheseDecodeNomenclatures(DB.Model):
    __tablename__ = 'v_synthese_decode_nomenclatures'
    __table_args__ = {'schema': 'gn_synthese'}
    id_synthese = DB.Column(DB.Integer, primary_key=True)
    nat_obj_geo = DB.Column(DB.Unicode)
    grp_typ = DB.Column(DB.Unicode)
    obs_method = DB.Column(DB.Unicode)
    obs_technique = DB.Column(DB.Unicode)
    bio_status = DB.Column(DB.Unicode)
    bio_condition = DB.Column(DB.Unicode)
    naturalness = DB.Column(DB.Unicode)
    exist_proof = DB.Column(DB.Unicode)
    valid_status = DB.Column(DB.Unicode)
    diffusion_level = DB.Column(DB.Unicode)
    life_stage = DB.Column(DB.Unicode)
    sex = DB.Column(DB.Unicode)
    obj_count = DB.Column(DB.Unicode)
    type_count = DB.Column(DB.Unicode)
    sensitivity = DB.Column(DB.Unicode)
    observation_status = DB.Column(DB.Unicode)
    blurring = DB.Column(DB.Unicode)
    source_status = DB.Column(DB.Unicode)


@serializable
@geoserializable
@shapeserializable
class Synthese(SyntheseCruved):
    __tablename__ = 'synthese'
    __table_args__ = {'schema': 'gn_synthese'}
    id_synthese = DB.Column(DB.Integer, ForeignKey(
        'gn_synthese.v_synthese_decode_nomenclatures.id_synthese'), primary_key=True)
    unique_id_sinp = DB.Column(UUID(as_uuid=True))
    unique_id_sinp_grp = DB.Column(UUID(as_uuid=True))
    id_source = DB.Column(DB.Integer)
    entity_source_pk_value = DB.Column(DB.Integer)
    id_dataset = DB.Column(DB.Integer)
    id_nomenclature_geo_object_nature = DB.Column(DB.Integer)
    id_nomenclature_grp_typ = DB.Column(DB.Integer)
    id_nomenclature_obs_meth = DB.Column(DB.Integer)
    id_nomenclature_obs_technique = DB.Column(DB.Integer)
    id_nomenclature_bio_status = DB.Column(DB.Integer)
    id_nomenclature_bio_condition = DB.Column(DB.Integer)
    id_nomenclature_naturalness = DB.Column(DB.Integer)
    id_nomenclature_exist_proof = DB.Column(DB.Integer)
    id_nomenclature_valid_status = DB.Column(DB.Integer)
    id_nomenclature_diffusion_level = DB.Column(DB.Integer)
    id_nomenclature_life_stage = DB.Column(DB.Integer)
    id_nomenclature_sex = DB.Column(DB.Integer)
    id_nomenclature_obj_count = DB.Column(DB.Integer)
    id_nomenclature_type_count = DB.Column(DB.Integer)
    id_nomenclature_sensitivity = DB.Column(DB.Integer)
    id_nomenclature_observation_status = DB.Column(DB.Integer)
    id_nomenclature_blurring = DB.Column(DB.Integer)
    id_nomenclature_source_status = DB.Column(DB.Integer)
    count_min = DB.Column(DB.Integer)
    count_max = DB.Column(DB.Integer)
    cd_nom = DB.Column(DB.Integer)
    nom_cite = DB.Column(DB.Unicode)
    meta_v_taxref = DB.Column(DB.Unicode)
    sample_number_proof = DB.Column(DB.Unicode)
    digital_proof = DB.Column(DB.Unicode)
    non_digital_proof = DB.Column(DB.Unicode)
    altitude_min = DB.Column(DB.Unicode)
    altitude_max = DB.Column(DB.Unicode)
    the_geom_4326 = DB.Column(Geometry('GEOMETRY', 4326))
    the_geom_point = DB.Column(Geometry('GEOMETRY', 4326))
    the_geom_local = DB.Column(Geometry('GEOMETRY', 2154))
    date_min = DB.Column(DB.DateTime)
    date_max = DB.Column(DB.DateTime)
    validator = DB.Column(DB.Unicode)
    validation_comment = DB.Column(DB.Unicode)
    observers = DB.Column(DB.Unicode)
    determiner = DB.Column(DB.Unicode)
    id_nomenclature_determination_method = DB.Column(DB.Integer)
    comments = DB.Column(DB.Unicode)
    meta_validation_date = DB.Column(DB.DateTime)
    meta_create_date = DB.Column(DB.DateTime)
    meta_update_date = DB.Column(DB.DateTime)
    last_action = DB.Column(DB.Unicode)

    def get_geofeature(self, recursif=True, columns=None):
        return self.as_geofeature('the_geom_4326', 'id_synthese', recursif, columns=columns)


@serializable
class CorAreaSynthese(DB.Model):
    __tablename__ = 'cor_area_synthese'
    __table_args__ = {'schema': 'gn_synthese'}
    id_synthese = DB.Column(DB.Integer, primary_key=True)
    id_area = DB.Column(DB.Integer)


@serializable
class DefaultsNomenclaturesValue(DB.Model):
    __tablename__ = 'defaults_nomenclatures_value'
    __table_args__ = {'schema': 'gn_synthese'}
    id_type = DB.Column(DB.Integer, primary_key=True)
    id_organism = DB.Column(DB.Integer, primary_key=True)
    regne = DB.Column(DB.Unicode, primary_key=True)
    group2_inpn = DB.Column(DB.Unicode, primary_key=True)
    id_nomenclature = DB.Column(DB.Integer)


@serializable
@geoserializable
class SyntheseOneRecord(SyntheseCruved):
    __tablename__ = 'synthese'
    __table_args__ = {'schema': 'gn_synthese', 'extend_existing': True}
    id_synthese = DB.Column(DB.Integer, primary_key=True)
    id_source = DB.Column(DB.Integer)
    unique_id_sinp = DB.Column(UUID(as_uuid=True))
    entity_source_pk_value = DB.Column(DB.Integer)
    id_dataset = DB.Column(DB.Integer)
    count_min = DB.Column(DB.Integer)
    count_max = DB.Column(DB.Integer)
    cd_nom = DB.Column(DB.Integer)
    nom_cite = DB.Column(DB.Unicode)
    sample_number_proof = DB.Column(DB.Unicode)
    digital_proof = DB.Column(DB.Unicode)
    non_digital_proof = DB.Column(DB.Unicode)
    altitude_min = DB.Column(DB.Integer)
    altitude_max = DB.Column(DB.Integer)
    the_geom_point = DB.Column(Geometry('GEOMETRY', 4326))
    the_geom_4326 = DB.Column(Geometry('GEOMETRY', 4326))
    date_min = DB.Column(DB.DateTime)
    date_max = DB.Column(DB.DateTime)
    observers = DB.Column(DB.Unicode)
    determiner = DB.Column(DB.Unicode)
    comments = DB.Column(DB.Unicode)
    occurrence_detail = DB.relationship(
        "VSyntheseDecodeNomenclatures",
        primaryjoin=(VSyntheseDecodeNomenclatures.id_synthese == id_synthese),
        foreign_keys=[id_synthese]
    )
    source = DB.relationship(
        'TSources',
        primaryjoin=(TSources.id_source == id_source),
        foreign_keys=[id_source]
    )
    areas = DB.relationship(
        'LAreas',
        secondary=corAreaSynthese,
        primaryjoin=(
            corAreaSynthese.c.id_synthese == id_synthese
        ),
        secondaryjoin=(corAreaSynthese.c.id_area == LAreas.id_area),
        foreign_keys=[
            corAreaSynthese.c.id_synthese,
            corAreaSynthese.c.id_area
        ]
    )
    dataset = DB.relationship(
        "TDatasets",
        primaryjoin=(TDatasets.id_dataset == id_dataset),
        foreign_keys=[id_dataset]
    )
    acquisition_framework = DB.relationship(
        "TAcquisitionFramework",
        uselist=False,
        secondary=TDatasets.__table__,
        primaryjoin=(TDatasets.id_dataset == id_dataset),
        secondaryjoin=(TDatasets.id_acquisition_framework == TAcquisitionFramework.id_acquisition_framework),
    )

    def get_geofeature(self, recursif=False):
        return self.as_geofeature('the_geom_4326', 'id_synthese', recursif)

@serializable
class VMTaxonsSyntheseAutocomplete(DB.Model):
    __tablename__ = 'vm_taxons_synthese_autocomplete'
    __table_args__ = {'schema': 'gn_synthese'}
    cd_nom = DB.Column(DB.Integer, primary_key=True)
    search_name = DB.Column(DB.Unicode, primary_key=True)
    cd_ref = DB.Column(DB.Integer)    
    nom_valide = DB.Column(DB.Unicode)
    lb_nom = DB.Column(DB.Unicode)
    regne = DB.Column(DB.Unicode)
    group2_inpn = DB.Column(DB.Unicode)

    def __repr__(self):
        return '<VMTaxonsSyntheseAutocomplete  %r>' % self.search_name