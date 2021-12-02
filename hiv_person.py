import dtk_hiv_intrahost as hiv
import random
from collections import defaultdict

population = defaultdict()
sex_dict = { 0: "male", 1: "female" }

class HivPerson():
    def __init__( self, age_in_years=None, sex=None ):
        if sex is None:
            sex = random.randint( 0, 1 )
        elif sex != 0 and sex != 1:
            raise ValueError( "Specified sex needs to be 0 (M) or 1 (F)." )
        self._sex = sex

        if age_in_years == None:
            age_in_years = random.random()*100
        elif age_in_years < 0 or age_in_years > 100:
            raise ValueError( "Specified age needs to be between 0 and 100." )
        print( f"Created new person with age {age_in_years:0.2f} and sex {sex_dict[sex]}" )
        self._id = hiv.create( ( sex, age_in_years*365, 1.0 ) )
        population[self._id] = self
        # hiv.set_ip( ( self._id, "Risk","LOW" ) ) # not supported yet

    @staticmethod
    def get_person_from_id( person_id ):
        # TBD: A little error-checking might be nice.
        return population[person_id]

    def give_intervention( self, iv ):
        individual_ptr = hiv.get_individual_for_iv( self._id )
        iv.distribute( individual_ptr )

    def id( self ):
        """
        Get id of person.
        """
        return self._id

    def sex( self ):
        """
        Get sex of person. A slight optimization here is that we don't call into 
        actual C++ instance since we have the sex value already cached.
        """
        return self._sex

    def force_infect( self ):
        """
            Initiate an HIV infection.
        """
        hiv.force_infect( self._id )

    def dead( self ):
        """
            Query if person is dead. If not hooked up to demographics module, this can only be from infection.
        """
        return hiv.is_dead( self._id )

    def cd4( self ):
        """
            Query person's CD4 count.
        """
        return( hiv.get_cd4( self._id ) )

    def update( self ):
        """
            Move time forward 1 timestep for this person.
        """
        hiv.update( self._id )

    def serialize( self ):
        """
            Get a json-serialized dictionary representing the full state of this person.
        """
        return hiv.serialize( self._id )

    def age( self ):
        """
            Query person's current age (in days).
        """
        return hiv.get_age( self._id )/365.0

    def infected( self ):
        """
            Query person's current HIV-infected status.
        """
        return hiv.is_infected( self._id )

    def infection_age( self ):
        """
            Get the age of the person's infection if any.
        """
        return hiv.get_infection_age( self._id )/365.0

    def infectiousness( self ):
        """
            Query person's current per-timestep viral shedding amount.
        """
        return hiv.get_infectiousness( self._id )

    def possible_mother( self ):
        """
            Query whether person can be a mother now.
        """
        return hiv.is_possible_mother( self._id )

    def immunity( self ):
        """
            Query person's immunity.
        """
        return hiv.get_immunity( self._id )

    def pregnant( self ):
        """
            Query person's immunity.
        """
        return hiv.is_pregnant( self._id )
