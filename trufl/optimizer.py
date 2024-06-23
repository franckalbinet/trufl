# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_optimizer.ipynb.

# %% auto 0
__all__ = ['Optimizer']

# %% ../nbs/02_optimizer.ipynb 3
import numpy as np
from .mcdm import score, normalize, weigh


# %% ../nbs/02_optimizer.ipynb 4
class Optimizer:
    def __init__(self, state):
        "Optimize the number of points for t. Provided the number of points to sample in t based on t-1, return values number of sample points."
        self.state = state
        return
    
        
    def build_matrix(self, polygon_list):
        "Build the matrix for the optimization"
        import numpy as np
        matrix = []
        self.list_id = polygon_list
        for polygon in polygon_list:
            polygon_state = self.state.get(loc_id=polygon, as_numpy=False)
            values = [var.value for var in polygon_state]
            matrix.append(values)
            
        decision_matrix = np.vstack(matrix)
        # build matrix with columns based on the needed criteria
        
        self.matrix = decision_matrix
        
        return decision_matrix
    
    def build_weight_vector(self, weight_vector, benefit_vector):
        "Build the weight vector for the optimization"
        self.weight_vector = weight_vector
        self.benefit_vector = benefit_vector
        return
        
        
    def rank(self,
        x_matrix,
        alt_names=None,
        is_benefit_x=None,
        n_method=None,
        w_vector=None,
        c_method=None,
        w_method="MW",
        s_method="SAW",
    ):
        """
        Return the ranking of the alternatives, in descending order, using the
        selected methods.
        """
        # Perform sanity checks
        x_matrix = np.array(x_matrix, dtype=np.float64)
        
        if alt_names is None:
            alt_names = ["" + str(i + 1) for i in range(x_matrix.shape[0])]
            
        if len(alt_names) != x_matrix.shape[0]:
            raise ValueError(
                "The number of names for the alternatives does not match the "
                + "number of rows in the decision matrix",
            )

        # If not specified, consider all criteria as benefit criteria
        if is_benefit_x is None:
            is_benefit_x = [True for _ in range(x_matrix.shape[1])]

        # Normalize the decision matrix using the selected method
        z_matrix, is_benefit_z = normalize(x_matrix, is_benefit_x, n_method)

        # Determine the weight of each criterion
        if w_vector is None:
            # Weigh each criterion using the selected methods
            w_vector = weigh(z_matrix, w_method, c_method)

        # Score each alternative using the selected method
        s_vector, desc_order = score(z_matrix, is_benefit_z, w_vector, s_method)

        # Get the indices of the sorted scores
        if desc_order:
            r_indices = np.argsort(-s_vector)
        else:
            r_indices = np.argsort(s_vector)

        # Create a list of tuples that includes the names of the alternatives and
        # their corresponding scores in descending order
        ranking = []
        for i in range(len(alt_names)):
            ranking.append((alt_names[r_indices[i]], s_vector[r_indices[i]]))

        return ranking

        
   

    


