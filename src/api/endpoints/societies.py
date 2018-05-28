"""Society Module."""

from flask import request
from flask_restplus import Resource

from api.utils.auth import token_required, roles_required
from api.utils.helpers import find_item, paginate_items, response_builder
from api.utils.marshmallow_schemas import cohort_schema, base_schema
from ..models import Society, Cohort


class SocietyResource(Resource):
    """To contain CRUD endpoints for Society."""

    @token_required
    @roles_required(["Success Ops"])
    def post(self):
        """Create a society."""
        payload = request.get_json(silent=True)
        if payload:
            try:
                name = payload["name"]
                color_scheme = payload["colorScheme"]
                logo = payload["logo"]
                photo = payload["photo"]
            except KeyError:
                return response_builder(dict(
                    status="fail",
                    message="Name, color scheme and logo are required"
                            " to create a society."
                    ), 400)

            # if no errors occur in assigning above
            society = Society(
                name=name, color_scheme=color_scheme, logo=logo, photo=photo
            )
            society.save()
            return response_builder(dict(
                status="success",
                data=society.serialize(),
                message="Society created successfully."
            ), 201)

        return response_builder(dict(
            status="fail",
            message="Data for creation must be provided"), 400)

    @token_required
    def get(self, society_id=None):
        """Get Society(ies) details."""
        if society_id:
            society = Society.query.get(society_id)
            return find_item(society)

        else:
            search_term = request.args.get('q')

            if search_term:
                society = Society.query.filter_by(name=search_term).first()
                return find_item(society)

            # if no search term has been passed, return all societies in DB
            societies = Society.query
            return paginate_items(societies)

    @classmethod
    @token_required
    @roles_required(["Success Ops"])
    def put(cls, society_id=None):
        """Edit Society details."""
        payload = request.get_json(silent=True)
        if payload:
            if not society_id:
                return response_builder(dict(
                    status="fail",
                    message="Society to be edited must be provided"), 400)

            society = Society.query.get(society_id)
            if society:
                try:
                    name = payload["name"] or None
                    color_scheme = payload["colorScheme"] or None
                    logo = payload["logo"] or None
                    photo = payload["photo"]or None
                    if name:
                        society.name = name
                    if color_scheme:
                        society.color = color_scheme
                    if photo:
                        society.photo = logo
                    if logo:
                        society.logo = photo
                    society.save()
                    return response_builder(dict(
                        data=dict(path=society.serialize()),
                        status="success",
                        message="Society edited successfully."
                    ), 200)

                except KeyError as e:
                    return response_builder(dict(
                        module="Society Module",
                        errors=e), 500)

            return response_builder(dict(
                                status="fail",
                                message="Society does not exist."), 404)

        # if payload does not exist
        return response_builder(dict(
            status="fail",
            message="Data for editing must be provided"), 400)

    @classmethod
    @token_required
    @roles_required(["Success Ops"])
    def delete(cls, society_id=None):
        """Delete Society."""
        if not society_id:
            return response_builder(dict(
                status="fail",
                message="Society id must be provided."), 400)

        society = Society.query.get(society_id)
        if not society:
            return response_builder(dict(
                status="fail",
                message="Society does not exist."), 404)

        society.delete()
        return response_builder(dict(
                status="success",
                message="Society deleted successfully."), 200)


class AddCohort(Resource):
    """Resource for adding cohorts to societies."""

    @token_required
    @roles_required(["Success Ops"])
    def put(self):
        """Assign a cohort to a society.

        Returns
            response (dict): key:status
        """
        payload = request.get_json(silent=True)

        if not payload or not ('societyId' in payload and 'cohortId' in payload):
            return response_builder(dict(
                message="Error societyId and cohortId are required."
            ), 400)

        society = Society.query.filter_by(
            uuid=payload.get('societyId')).first()
        if not society:
            return response_builder(dict(
                message="Error Invalid societyId."
            ), 400)

        cohort = Cohort.query.filter_by(uuid=payload.get('cohortId')).first()
        if not cohort:
            return response_builder(dict(
                message="Error Invalid cohortId."
            ), 400)

        if cohort.society_id == society.uuid:
            return response_builder(dict(
                message="Cohort already in society."
            ), 409)

        society.cohorts.append(cohort)
        society.save()
        cohort.save()

        cohort_data = cohort_schema.dump(cohort).data
        cohort_meta_data = {
                'society': base_schema.dump(society).data,
                'country': base_schema.dump(cohort.country).data
                }
        cohort_data['meta'] = cohort_meta_data

        return response_builder(dict(
            message="Cohort added to society succesfully",
            data=cohort_data
        ), 200)
