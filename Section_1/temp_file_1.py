class Recipe:
    """
    A list of instructions for transforming one set of containers into another. The intended workflow is to declare
    the source containers, enumerate the desired transformations, and call recipe.bake(). The name of each object used
    by the Recipe must be unique. This method will ensure that all solid and liquid handling instructions are valid.
    If they are indeed valid, then the updated containers will be generated. Once recipe.bake() has been called, no
    more instructions can be added and the Recipe is considered immutable.

    Attributes:
        locked (boolean): Is the recipe locked from changes?
        steps (list): A list of steps to be completed upon bake() bring called.
        used (list): A list of Containers and Plates to be used in the recipe.
        results (dict): A dictionary used in bake to return the mutated objects.
        stages (dict): A dictionary of stages in the recipe.
    """


[docs]
    def __init__(self):
        self.results: dict[str, Container | Plate | PlateSlicer] = {}
        self.steps: list[RecipeStep] = []
        self.stages: dict[str, slice] = {'all': slice(None, None)}
        self.current_stage = 'all'
        self.current_stage_start = 0
        self.locked = False
        self.used = set()




[docs]
    def start_stage(self, name: str) -> None:
        """
        Start a new stage in the recipe.

        Args:
            name: Name of the stage.

        """
        if self.locked:
            raise RuntimeError("This recipe is locked.")
        if name in self.stages:
            raise ValueError("Stage name already exists.")
        if self.current_stage != 'all':
            raise ValueError("Cannot start a new stage without ending the current one.")
        self.current_stage = name
        self.current_stage_start = len(self.steps)




[docs]
    def end_stage(self, name: str) -> None:
        """
        End the current stage in the recipe.

        Args:
            name: Name of the stage.

        """
        if self.locked:
            raise RuntimeError("This recipe is locked.")
        if self.current_stage != name:
            raise ValueError("Current stage does not match name.")

        self.stages[name] = slice(self.current_stage_start, len(self.steps))
        self.current_stage = 'all'




[docs]
    def uses(self, *args: Container | Plate | Iterable[Container | Plate]) -> Recipe:
        """
        Declare *args (iterable of Containers and Plates) as being used in the recipe.
        """
        if self.locked:
            raise RuntimeError("This recipe is locked.")
        for arg in args:
            if isinstance(arg, (Container, Plate)):
                if arg.name not in self.results:
                    self.results[arg.name] = deepcopy(arg)
                else:
                    raise ValueError(f"An object with the name: \"{arg.name}\" is already in use.")
            elif isinstance(arg, Iterable):
                unpacked = list(arg)
                if not all(isinstance(elem, (Container, Plate)) for elem in unpacked):
                    raise TypeError("Invalid type in iterable.")
                self.uses(*unpacked)
            else:
                raise TypeError("Invalid type.")
        return self




[docs]
    def transfer(self, source: Container | Plate | PlateSlicer, destination: Container | Plate | PlateSlicer,
                 quantity: str) -> None:
        """
        Adds a step to the recipe which will move quantity from source to destination.
        Note that all Substances in the source will be transferred in proportion to their respective ratios.

        """
        if self.locked:
            raise RuntimeError("This recipe is locked.")
        if not isinstance(destination, (Container, Plate, PlateSlicer)):
            raise TypeError("Invalid destination type.")
        if not isinstance(source, (Container, Plate, PlateSlicer)):
            raise TypeError("Invalid source type.")
        if (source.plate.name if isinstance(source, PlateSlicer) else source.name) not in self.results:
            raise ValueError("Source not found in declared uses.")
        destination_name = destination.plate.name if isinstance(destination, PlateSlicer) else destination.name
        if destination_name not in self.results:
            raise ValueError(f"Destination {destination_name} has not been previously declared for use.")
        if not isinstance(quantity, str):
            raise TypeError("Volume must be a str. ('5 mL')")
        if isinstance(source, Plate):
            source = source[:]
        if isinstance(destination, Plate):
            destination = destination[:]
        self.steps.append(RecipeStep(self, 'transfer', source, destination, quantity))




[docs]
    def create_container(self, name: str, max_volume: str = 'inf L',
                         initial_contents: Iterable[tuple[Substance, str]] | None = None) -> Container:

        """
        Adds a step to the recipe which creates a container.

        Arguments:
            name: Name of container
            max_volume: Maximum volume that can be stored in the container. ('10 mL')
            initial_contents: (optional) Iterable of tuples of the form (Substance, quantity)

        Returns:
            A new Container so that it may be used in later recipe steps.
        """
        if self.locked:
            raise RuntimeError("This recipe is locked.")
        if not isinstance(name, str):
            raise TypeError("Name must be a str.")
        if not isinstance(max_volume, str):
            raise TypeError("Maximum volume must be a str.")

        if initial_contents:
            if not isinstance(initial_contents, Iterable):
                raise TypeError("Initial contents must be iterable.")
            if not all(isinstance(elem, tuple) and len(elem) == 2 for elem in initial_contents):
                raise TypeError("Elements of initial_contents must be of the form (Substance, quantity.)")
            for substance, quantity in initial_contents:
                if not isinstance(substance, Substance):
                    raise TypeError("Containers can only be created from substances.")
                if not isinstance(quantity, str):
                    raise TypeError("Quantity must be a str. ('10 mL')")
        new_container = Container(name, max_volume)
        self.uses(new_container)
        self.steps.append(RecipeStep(self, 'create_container', None, new_container, max_volume, initial_contents))

        return new_container




[docs]
    def create_solution(self, solute: Substance | Iterable[Substance], solvent: Substance | Container,
                        name=None, **kwargs) -> Container:
        """
        Adds a step to the recipe which creates a solution.

        Two out of concentration, quantity, and total_quantity must be specified.

        Multiple solutes can be, optionally, provided as a list. Each solute will have the desired concentration
        or quantity in the final solution.

        If one value is specified for concentration or quantity and multiple solutes are provided, the value will be
        used for all solutes.

        Arguments:
            solute: What to dissolve. Can be a single Substance or an iterable of Substances.
            solvent: What to dissolve with. Can be a Substance or a Container.
            name: Optional name for new container.
            concentration: Desired concentration(s). ('1 M', '0.1 umol/10 uL', etc.)
            quantity: Desired quantity of solute(s). ('3 mL', '10 g')
            total_quantity: Desired total quantity. ('3 mL', '10 g')


        Returns:
            A new Container so that it may be used in later recipe steps.
        """

        if not isinstance(solute, Substance):
            raise TypeError("Solute must be a Substance.")
        if not isinstance(solvent, Substance):
            raise TypeError("Solvent must be a Substance.")
        if name and not isinstance(name, str):
            raise TypeError("Name must be a str.")

        if 'concentration' in kwargs and not isinstance(kwargs['concentration'], str):
            raise TypeError("Concentration must be a str.")
        if 'quantity' in kwargs and not isinstance(kwargs['quantity'], str):
            raise TypeError("Quantity must be a str.")
        if 'total_quantity' in kwargs and not isinstance(kwargs['total_quantity'], str):
            raise TypeError("Total quantity must be a str.")
        if ('concentration' in kwargs) + ('total_quantity' in kwargs) + ('quantity' in kwargs) != 2:
            raise ValueError("Must specify two values out of concentration, quantity, and total quantity.")

        if not name:
            name = f"solution of {solute.name} in {solvent.name}"

        new_container = Container(name)
        self.uses(new_container)
        self.steps.append(RecipeStep(self, 'solution', None, new_container, solute, solvent, kwargs))

        return new_container




[docs]
    def create_solution_from(self, source: Container, solute: Substance, concentration: str, solvent: Substance,
                             quantity: str, name=None) -> Container:
        """
        Adds a step to create a diluted solution from an existing solution.


        Arguments:
            source: Solution to dilute.
            solute: What to dissolve.
            concentration: Desired concentration. ('1 M', '0.1 umol/10 uL', etc.)
            solvent: What to dissolve with.
            quantity: Desired total quantity. ('3 mL', '10 g')
            name: Optional name for new container.

        Returns:
            A new Container so that it may be used in later recipe steps.
        """

        if not isinstance(source, Container):
            raise TypeError("Source must be a Container.")
        if not isinstance(solute, Substance):
            raise TypeError("Solute must be a Substance.")
        if not isinstance(concentration, str):
            raise TypeError("Concentration must be a str.")
        if not isinstance(solvent, Substance):
            raise TypeError("Solvent must be a Substance.")
        if not isinstance(quantity, str):
            raise TypeError("Quantity must be a str.")
        if name and not isinstance(name, str):
            raise TypeError("Name must be a str.")

        quantity_value, quantity_unit = Unit.parse_quantity(quantity)
        if quantity_value <= 0:
            raise ValueError("Quantity must be positive.")

        if not name:
            name = f"solution of {solute.name} in {solvent.name}"

        new_ratio, numerator, denominator = Unit.calculate_concentration_ratio(solute, concentration, solvent)
        if new_ratio <= 0:
            raise ValueError("Solution is impossible to create.")

        new_container = Container(name, max_volume=f"{source.max_volume} {config.volume_storage_unit}")
        self.uses(new_container)
        self.steps.append(RecipeStep(self, 'solution_from', source, new_container,
                                     solute, concentration, solvent, quantity))

        return new_container




[docs]
    def remove(self, destination: Container | Plate | PlateSlicer, what=Substance.LIQUID) -> None:
        """
        Adds a step to removes substances from destination.

        Arguments:
            destination: What to remove from.
            what: What to remove. Can be a type of substance or a specific substance. Defaults to LIQUID.
        """

        if isinstance(destination, PlateSlicer):
            if destination.plate.name not in self.results:
                raise ValueError(f"Destination {destination.plate.name} has not been previously declared for use.")
        elif isinstance(destination, (Container, Plate)):
            if destination.name not in self.results:
                raise ValueError(f"Destination {destination.name} has not been previously declared for use.")
        else:
            raise TypeError(f"Invalid destination type: {type(destination)}")

        self.steps.append(RecipeStep(self, 'remove', None, destination, what))




[docs]
    def dilute(self, destination: Container, solute: Substance,
               concentration: str, solvent: Substance, new_name=None) -> None:
        """
        Adds a step to dilute `solute` in `destination` to `concentration`.

        Args:
            destination: Container to dilute.
            solute: Substance which is subject to dilution.
            concentration: Desired concentration in mol/L.
            solvent: What to dilute with.
            new_name: Optional name for new container.
        """

        if not isinstance(solute, Substance):
            raise TypeError("Solute must be a Substance.")
        if not isinstance(concentration, str):
            raise TypeError("Concentration must be a float.")
        if not isinstance(solvent, Substance):
            raise TypeError("Solvent must be a substance.")
        if new_name and not isinstance(new_name, str):
            raise TypeError("New name must be a str.")
        if not isinstance(destination, Container):
            raise TypeError("Destination must be a container.")
        if destination.name not in self.results:
            raise ValueError(f"Destination {destination.name} has not been previously declared for use.")
        # if solute not in destination.contents:
        #     raise ValueError(f"Container does not contain {solute.name}.")

        ratio, *_ = Unit.calculate_concentration_ratio(solute, concentration, solvent)
        if ratio <= 0:
            raise ValueError("Concentration is impossible to create.")

        if solute.is_enzyme():
            # TODO: Support this.
            raise ValueError("Not currently supported.")

        self.steps.append(RecipeStep(self, 'dilute', None, destination, solute, concentration, solvent, new_name))




[docs]
    def fill_to(self, destination: Container | Plate | PlateSlicer, solvent: Substance, quantity: str) -> None:
        """
        Adds a step to fill `destination` container/plate/slice with `solvent` up to `quantity`.

        Args:
            destination: Container/Plate/Slice to fill.
            solvent: Substance to use to fill.
            quantity: Desired final quantity in container.

        """
        if isinstance(destination, PlateSlicer):
            if destination.plate.name not in self.results:
                raise ValueError(f"Destination {destination.plate.name} has not been previously declared for use.")
        elif isinstance(destination, (Container, Plate)):
            if destination.name not in self.results:
                raise ValueError(f"Destination {destination.name} has not been previously declared for use.")
        else:
            raise TypeError(f"Invalid destination type: {type(destination)}")
        if not isinstance(solvent, Substance):
            raise TypeError("Solvent must be a substance.")
        if not isinstance(quantity, str):
            raise TypeError("Quantity must be a str.")

        self.steps.append(RecipeStep(self, 'fill_to', None, destination, solvent, quantity))




[docs]
    def bake(self) -> dict[str, Container | Plate]:
        """
        Completes steps stored in recipe.
        Checks validity of each step and ensures all declared objects have been used.
        Locks Recipe from further modification.

        Returns:
            Copies of all used objects in the order they were declared.

        """
        if self.locked:
            raise RuntimeError("Recipe has already been baked.")

        # Implicitly end the current stage
        if self.current_stage != 'all':
            self.end_stage(self.current_stage)

        for step in self.steps:
            # Keep track of what was used in each step
            for elem in step.frm + step.to:
                if isinstance(elem, PlateSlicer):
                    step.objects_used.add(elem.plate.name)
                elif isinstance(elem, (Container, Plate)):
                    step.objects_used.add(elem.name)

            step.frm_slice = step.frm[0] if isinstance(step.frm[0], PlateSlicer) else None
            step.to_slice = step.to[0] if isinstance(step.to[0], PlateSlicer) else None

            operator = step.operator
            if operator == 'create_container':
                dest = step.to[0]
                dest_name = dest.name
                step.frm.append(None)
                max_volume, initial_contents = step.operands
                step.to[0] = self.results[dest_name]
                self.used.add(dest_name)
                self.results[dest_name] = Container(dest_name, max_volume, initial_contents)
                step.substances_used = self.results[dest_name].get_substances()
                step.to.append(self.results[dest_name])
                step.instructions = f"Create container '{dest_name}'."
            elif operator == 'transfer':
                source = step.frm[0]
                source_name = source.plate.name if isinstance(source, PlateSlicer) else source.name
                dest = step.to[0]
                dest_name = dest.plate.name if isinstance(dest, PlateSlicer) else dest.name
                quantity, = step.operands

                step.instructions = f"""Transfer {quantity} from '{str(source) if isinstance(source, PlateSlicer) else
                source_name}' to '{str(dest) if isinstance(dest, PlateSlicer) else dest_name}'."""

                self.used.add(source_name)
                self.used.add(dest_name)

                # containers and such can change while baking the recipe
                if isinstance(source, PlateSlicer):
                    source = deepcopy(source)
                    source.plate = self.results[source_name]
                    step.frm[0] = source.plate
                else:
                    source = self.results[source_name]
                    step.frm[0] = source

                step.substances_used = source.get_substances()

                if isinstance(dest, PlateSlicer):
                    dest = deepcopy(dest)
                    dest.plate = self.results[dest_name]
                    step.to[0] = dest.plate
                else:
                    dest = self.results[dest_name]
                    step.to[0] = dest

                if isinstance(dest, Container):
                    source, dest = Container.transfer(source, dest, quantity)
                elif isinstance(dest, PlateSlicer):
                    source, dest = Plate.transfer(source, dest, quantity)

                self.results[source_name] = source if not isinstance(source, PlateSlicer) else source.plate
                self.results[dest_name] = dest if not isinstance(dest, PlateSlicer) else dest.plate

                step.frm.append(self.results[source_name])
                step.to.append(self.results[dest_name])
            elif operator == 'solution':
                dest = step.to[0]
                dest_name = dest.name
                step.frm.append(None)
                solute, solvent, kwargs = step.operands
                # kwargs should have two out of concentration, quantity, and total_quantity
                if 'concentration' in kwargs and 'total_quantity' in kwargs:
                    step.instructions = f"""Create a solution of '{solute.name}' in '{solvent.name
                    }' with a concentration of {kwargs['concentration']
                    } and a total quantity of {kwargs['total_quantity']}."""
                elif 'concentration' in kwargs and 'quantity' in kwargs:
                    step.instructions = f"""Create a solution of '{solute.name}' in '{solvent.name
                    }' with a concentration of {kwargs['concentration']
                    } and a quantity of {kwargs['quantity']}."""
                elif 'quantity' in kwargs and 'total_quantity' in kwargs:
                    step.instructions = f"""Create a solution of '{solute.name}' in '{solvent.name
                    }' with a total quantity of {kwargs['total_quantity']
                    } and a quantity of {kwargs['quantity']}."""

                step.to[0] = self.results[dest_name]
                self.used.add(dest_name)
                self.results[dest_name] = Container.create_solution(solute, solvent, dest_name, **kwargs)
                step.substances_used = self.results[dest_name].get_substances()
                step.to.append(self.results[dest_name])
            elif operator == 'solution_from':
                source = step.frm[0]
                source_name = source.name
                dest = step.to[0]
                dest_name = dest.name
                solute, concentration, solvent, quantity = step.operands
                step.frm[0] = self.results[source_name]
                step.to[0] = self.results[dest_name]
                step.instructions = f"""Create {quantity} of a {concentration} solution of '{solute.name
                }' in '{solvent.name}' from '{source_name}'."""
                self.used.add(source_name)
                self.used.add(dest_name)
                source = self.results[source_name]
                self.results[source_name], self.results[dest_name] = \
                    Container.create_solution_from(source, solute, concentration, solvent, quantity, dest.name)
                step.substances_used = self.results[dest_name].get_substances()
                step.frm.append(self.results[source_name])
                step.to.append(self.results[dest_name])
            elif operator == 'remove':
                dest = step.to[0]
                step.frm.append(None)
                what, = step.operands
                dest_name = dest.plate.name if isinstance(dest, PlateSlicer) else dest.name
                step.to[0] = self.results[dest_name]
                self.used.add(dest_name)

                if isinstance(dest, PlateSlicer):
                    dest = deepcopy(dest)
                    dest.plate = self.results[dest_name]
                else:
                    dest = self.results[dest_name]

                if isinstance(what, Substance):
                    step.instructions = f"Remove {what.name} from '{dest_name}'."
                else:
                    step.instructions = f"Remove all {Substance.classes[what]} from '{dest_name}'."
                self.results[dest_name] = dest.remove(what)
                step.to.append(self.results[dest_name])
                # substances_used is everything that is in step.to[0] but not in step.to[1]
                step.substances_used = set.difference(step.to[0].get_substances(), step.to[1].get_substances())
                if isinstance(dest, Container):
                    step.trash = {substance: step.to[0].contents[substance] for substance in step.substances_used}
                else:  # Plate
                    for well in step.to[0].wells.flatten():
                        for substance in step.substances_used:
                            step.trash[substance] = step.trash.get(substance, 0.) + well.contents.get(substance, 0.)
            elif operator == 'dilute':
                dest = step.to[0]
                dest_name = dest.name
                solute, concentration, solvent, new_name = step.operands
                step.frm.append(None)
                step.to[0] = self.results[dest_name]
                self.used.add(dest_name)
                self.results[dest_name] = self.results[dest_name].dilute(solute, concentration, solvent, new_name)
                amount_added = self.results[dest_name].contents[solvent] - step.to[0].contents.get(solvent, 0)
                amount_added = Unit.convert_from(solvent, amount_added, config.moles_storage_unit, 'L')
                amount_added, unit = Unit.get_human_readable_unit(amount_added, 'L')
                precision = config.precisions[unit] if unit in config.precisions else config.precisions['default']
                step.instructions = (f"Dilute '{solute.name}' in '{dest_name}' to {concentration}" +
                                     f" by adding {round(amount_added, precision)} {unit} of '{solvent.name}'.")
                step.substances_used.add(solvent)
                step.to.append(self.results[dest_name])
            elif operator == 'fill_to':
                dest = step.to[0]
                dest_name = dest.plate.name if isinstance(dest, PlateSlicer) else dest.name
                solvent, quantity = step.operands
                step.frm.append(None)
                step.to[0] = self.results[dest_name]
                self.used.add(dest_name)
                self.results[dest_name] = step.to[0].fill_to(solvent, quantity)
                step.to.append(self.results[dest_name])
                if isinstance(dest, Container):
                    amount_added = self.results[dest_name].contents[solvent] - step.to[0].contents.get(solvent, 0)
                    amount_added = Unit.convert_from(solvent, amount_added, config.moles_storage_unit, 'L')
                    amount_added, unit = Unit.get_human_readable_unit(amount_added, 'L')
                    precision = config.precisions[unit] if unit in config.precisions else config.precisions['default']
                    step.instructions = (f"Fill '{dest.name}' with '{solvent.name}' up to {quantity}"
                                         f" by adding {round(amount_added, precision)} {unit}.")
                else:  # PlateSlicer
                    def collapse(wells, plate):
                        result = []
                        row_run = col_run = None
                        start_well = end_well = wells[0]
                        for well in wells[1:]:
                            if row_run is not None:
                                if well[0] == row_run and well[1] == end_well[1] + 1:
                                    end_well = well
                                else:
                                    row_run = None
                                    result.append(
                                        f"{plate.row_names[start_well[0]]}{plate.column_names[start_well[1]]}:"
                                        f"{plate.row_names[end_well[0]]}{plate.column_names[end_well[1]]}")
                                    start_well = end_well = well
                            elif col_run is not None:
                                if well[1] == col_run and well[0] == end_well[0] + 1:
                                    end_well = well
                                else:
                                    col_run = None
                                    result.append(
                                        f"{plate.row_names[start_well[0]]}{plate.column_names[start_well[1]]}:"
                                        f"{plate.row_names[end_well[0]]}{plate.column_names[end_well[1]]}")
                                    start_well = end_well = well
                            elif well[0] == end_well[0] and well[1] == end_well[1] + 1:
                                end_well = well
                                row_run = well[0]
                            elif well[1] == end_well[1] and well[0] == end_well[0] + 1:
                                end_well = well
                                col_run = well[1]
                            else:
                                result.append(f"{plate.row_names[start_well[0]]}{plate.column_names[start_well[1]]}")
                                start_well = end_well = well
                        if row_run is not None or col_run is not None:
                            result.append(f"{plate.row_names[start_well[0]]}{plate.column_names[start_well[1]]}:"
                                          f"{plate.row_names[end_well[0]]}{plate.column_names[end_well[1]]}")
                        if start_well == end_well:
                            result.append(f"{plate.row_names[start_well[0]]}{plate.column_names[start_well[1]]}")
                        return result

                    amounts = dict()
                    plate = step.to[0]
                    for row in range(plate.n_rows):
                        for col in range(plate.n_columns):
                            amount_added = self.results[dest_name].wells[row, col].contents[solvent] - \
                                           plate.wells[row, col].contents.get(solvent, 0)
                            amount_added = Unit.convert_from(solvent, amount_added, config.moles_storage_unit, 'uL')
                            amounts[(row, col)] = round(amount_added, config.internal_precision)
                    max_amount = max(amounts.values())
                    _, unit = Unit.get_human_readable_unit(max_amount / 1e6, 'L')
                    multiplier = 1e-6 / Unit.convert_prefix_to_multiplier(unit[:-1])
                    precision = config.precisions[unit] if unit in config.precisions else config.precisions['default']
                    amounts_transpose = dict()
                    for address, amount in amounts.items():
                        amount = round(amount * multiplier, precision)
                        if amount == 0.:
                            continue
                        if amount not in amounts_transpose:
                            amounts_transpose[amount] = []
                        amounts_transpose[amount].append(address)
                    step.instructions = f"Fill '{dest.name}' with '{solvent.name}' up to {quantity} by adding: "
                    amount_strings = []
                    for amount, addresses in amounts_transpose.items():
                        addresses = collapse(addresses, plate)
                        amount_strings.append(f"{amount} {unit} to [{', '.join(addresses)}]")
                    step.instructions += ', '.join(amount_strings) + "."

                if isinstance(dest, PlateSlicer):
                    dest = deepcopy(dest)
                    dest.plate = self.results[dest_name]
                else:
                    dest = self.results[dest_name]

                self.results[dest_name] = dest.fill_to(solvent, quantity)
                step.substances_used.add(solvent)
                step.to.append(self.results[dest_name])

        if len(self.used) != len(self.results):
            raise ValueError("Something declared as used wasn't used.")
        self.locked = True
        # All the PlateSlicers should have been resolved into Plates by now
        assert all(isinstance(elem, (Container, Plate)) for elem in self.results.values())
        return self.results




[docs]
    def get_substance_used(self, substance: Substance, timeframe: str = 'all', unit: str = None,
                           destinations: Iterable[Container | Plate] | str = "plates"):
        """
        Returns the amount of substance used in the recipe.

        Args:
            substance: Substance to check.
            timeframe: 'before' or 'during'. Before refers to the initial state of the containers aka recipe "prep", and
            during refers to
            unit: Unit to return amount in.
            destinations: Containers or plates to check. Defaults to "plates".

        Returns: Amount of substance used in the recipe.

        """
        if unit is None:
            unit = 'U' if substance.is_enzyme() else config.moles_display_unit

        from_unit = 'U' if substance.is_enzyme() else config.moles_storage_unit

        dest_names = set()
        if destinations == "plates":
            dest_names = set(elem.name for elem in self.results.values() if isinstance(elem, Plate))
        elif isinstance(destinations, Iterable):
            for container in destinations:
                if container.name not in self.used:
                    raise ValueError(f"Destination {container.name} was not used in the recipe.")
                dest_names.add(container.name)
        else:
            raise ValueError("Invalid destinations.")

        delta = 0

        if timeframe not in self.stages.keys():
            raise ValueError("Invalid timeframe")

        stage_steps = self.steps[self.stages[timeframe]]
        for step in stage_steps:
            if substance not in step.substances_used:
                continue

            before_substances = 0
            after_substances = 0
            if step.to[0] is not None and step.to[0].name in dest_names:
                if isinstance(step.to[0], Plate):
                    before_substances += sum(well.contents.get(substance, 0) for well in step.to[0].wells.flatten())
                    after_substances += sum(well.contents.get(substance, 0) for well in step.to[1].wells.flatten())
                else:  # Container
                    before_substances += step.to[0].contents.get(substance, 0)
                    after_substances += step.to[1].contents.get(substance, 0)
            if step.frm[0] is not None and step.frm[0].name in dest_names:
                if isinstance(step.frm[0], Plate):
                    before_substances += sum(well.contents.get(substance, 0) for well in step.frm[0].wells.flatten())
                    after_substances += sum(well.contents.get(substance, 0) for well in step.frm[1].wells.flatten())
                else:  # Container
                    before_substances += step.frm[0].contents.get(substance, 0)
                    after_substances += step.frm[1].contents.get(substance, 0)
            after_substances += step.trash.get(substance, 0)
            delta += after_substances - before_substances

        if delta < 0:
            raise ValueError(
                f"Destination containers contain {-delta} {from_unit} less of substance {substance}" +
                " after stage {timeframe}. Did you specify the correct destinations?")
        precision = config.precisions[unit] if unit in config.precisions else config.precisions['default']
        return round(Unit.convert(substance, f'{delta} {from_unit}', unit), precision)




[docs]
    def get_container_flows(self, container: Container | Plate, timeframe: str = 'all', unit: str | None = None) -> \
            dict[str, (int | str)]:
        """
        Returns the inflow and outflow of a container in the recipe.

        Args:
            container: Container to check.
            timeframe: 'all' or a stage defined in the recipe.
            unit: Unit to return amount in.
        """

        def helper(entry):
            substance, quantity = entry
            return Unit.convert_from(substance, quantity, 'U' if substance.is_enzyme() else config.moles_storage_unit,
                                     unit)

        def plate_helper(container):
            entry = container.contents.items()
            return sum(map(helper, entry))

        if unit is None:
            unit = config.volume_display_unit
        if not isinstance(unit, str):
            raise TypeError("Unit must be a str.")
        if not isinstance(container, Container) and not isinstance(container, Plate):
            raise TypeError("Container must be a Container or a Plate.")
        if not isinstance(timeframe, str):
            raise TypeError("Timeframe must be a str.")
        if timeframe not in self.stages.keys():
            raise ValueError("Invalid Timeframe")
        steps = self.steps[self.stages[timeframe]]
        flows = {"in": 0, "out": 0}
        if isinstance(container, Plate):
            flows = {"in": np.zeros(container.wells.shape), "out": np.zeros(container.wells.shape)}
        for step in steps:
            if container.name in step.objects_used:
                if isinstance(step.to[0], Container) and step.to[0].name == container.name:
                    if step.trash:
                        flows["out"] += sum(map(helper, step.trash.items()))
                    else:
                        flows["in"] += (sum(map(helper, step.to[1].contents.items())) -
                                        sum(map(helper, step.to[0].contents.items())))
                if isinstance(step.to[0], Plate) and step.to[0].name == container.name:
                    if step.trash:
                        flows["out"] += sum(map(helper, step.trash.items()))
                    else:
                        vfunc = np.vectorize(plate_helper)
                        flows["in"] += vfunc(step.to[1].wells) - vfunc(step.to[0].wells)
                if isinstance(step.frm[0], Container) and step.frm[0].name == container.name:
                    flows["out"] += (sum(map(helper, step.frm[0].contents.items())) -
                                     sum(map(helper, step.frm[1].contents.items())))
                if isinstance(step.frm[0], Plate) and step.frm[0].name == container.name:
                    vfunc = np.vectorize(plate_helper)
                    flows["out"] += vfunc(step.frm[0].wells) - vfunc(step.frm[1].wells)
        precision = config.precisions[unit] if unit in config.precisions else config.precisions['default']
        for key in flows:
            flows[key] = round(flows[key], precision)

        return flows




[docs]
    def get_amount_remaining(self, container: Container | Plate, timeframe: str = 'all',
                             unit: str | None = None, mode: str = 'after') -> float:

        def conversion_helper(entry):
            substance, quantity = entry
            return Unit.convert_from(substance, quantity, 'U' if substance.is_enzyme() else config.moles_storage_unit,
                                     unit)

        def plate_helper(well):
            entry = well.contents.items()
            return sum(map(conversion_helper, entry))

        def container_helper(container):
            if isinstance(container, Container):
                entry = container.contents.items()
                return sum(map(conversion_helper, entry))
            elif isinstance(container, Plate):
                vfunc = np.vectorize(plate_helper)
                return vfunc(container.wells)

        if unit is None:
            unit = config.volume_display_unit
        if not isinstance(unit, str):
            raise TypeError("Unit must be a str.")
        if not isinstance(container, Container) and not isinstance(container, Plate):
            raise TypeError("Container must be a Container or a Plate.")
        if not isinstance(timeframe, str):
            raise TypeError("Timeframe must be a str.")
        if timeframe not in self.stages.keys():
            raise ValueError("Invalid Timeframe")

        steps = self.steps[self.stages[timeframe]]
        if mode == 'after':
            steps = reversed(steps)

        query_container = None
        for step in steps:
            if container.name in step.objects_used:
                if step.to[0].name == container.name:
                    if mode == 'after':
                        query_container = step.to[1]
                    else:
                        query_container = step.to[0]
                else:
                    if mode == 'after':
                        query_container = step.frm[1]
                    else:
                        query_container = step.frm[0]
                return container_helper(query_container)




[docs]
    def visualize(self, what: Plate, mode: str, unit: str, timeframe: (int | str | RecipeStep) = 'all',
                  substance: (str | Substance) = 'all', cmap: str = None) \
            -> str | pandas.io.formats.style.Styler:
        """

        Provide visualization of what happened during the step.

        Args:
            what: Plate we are interested in.
            mode: 'delta', or 'final'
            timeframe: Number of the step or the name of the stage to visualize.
            unit: Unit we are interested in. ('mmol', 'uL', 'mg')
            substance: Substance we are interested in. ('all', water, ATP)
            cmap: Colormap to use. Defaults to default_colormap from config.

        Returns: A dataframe with the requested information.
        """
        if not isinstance(what, Plate):
            raise TypeError("What must be a Plate.")
        if mode not in ['delta', 'final']:
            raise ValueError("Invalid mode.")
        if not isinstance(timeframe, (int, str, RecipeStep)):
            raise TypeError("When must be an int or str.")
        if isinstance(timeframe, str) and timeframe not in self.stages:
            raise ValueError("Invalid stage.")
        if not isinstance(unit, str):
            raise TypeError("Unit must be a str.")
        if substance != 'all' and not isinstance(substance, Substance):
            raise TypeError("Substance must be a Substance or 'all'")
        if cmap is None:
            cmap = config.default_colormap
        if not isinstance(cmap, str):
            raise TypeError("Colormap must be a str.")

        def helper(elem):
            """ Returns amount of substance in elem. """
            if substance == 'all':
                amount = 0
                for subst, quantity in elem.contents.items():
                    substance_unit = 'U' if subst.is_enzyme() else config.moles_storage_unit
                    amount += Unit.convert_from(subst, quantity, substance_unit, unit)
                return amount
            else:
                substance_unit = 'U' if substance.is_enzyme() else config.moles_storage_unit
                return Unit.convert_from(substance, elem.contents.get(substance, 0), substance_unit, unit)

        if isinstance(timeframe, RecipeStep):
            start_index = self.steps.index(timeframe)
            end_index = start_index + 1
        elif isinstance(timeframe, str):
            start_index = self.stages[timeframe].start
            end_index = self.stages[timeframe].stop
            if start_index is None:
                start_index = 0
            if end_index is None:
                end_index = len(self.steps)
        else:
            if timeframe >= len(self.steps):
                raise ValueError("Invalid step number.")
            if timeframe < 0:
                timeframe = max(0, len(self.steps) + timeframe)
            start_index = timeframe
            end_index = timeframe + 1

        start = None
        end = None
        for i in range(start_index, end_index):
            step = self.steps[i]
            if what.name in step.objects_used:
                start = i
                break
        for i in range(end_index - 1, start_index - 1, -1):
            step = self.steps[i]
            if what.name in step.objects_used:
                end = i
                break
        if start is None or end is None:
            return "This plate was not used in the specified timeframe."

        if mode == 'delta':
            before_data = None
            if what.name == self.steps[start].frm[0].name:
                before_data = self.steps[start].frm[0][:].get_dataframe()
            elif what.name == self.steps[start].to[0].name:
                before_data = self.steps[start].to[0][:].get_dataframe()
            before_data = before_data.applymap(numpy.vectorize(helper, cache=True, otypes='d'))
            after_data = None
            if what.name == self.steps[end].frm[1].name:
                after_data = self.steps[end].frm[1][:].get_dataframe()
            elif what.name == self.steps[end].to[1].name:
                after_data = self.steps[end].to[1][:].get_dataframe()
            after_data = after_data.applymap(numpy.vectorize(helper, cache=True, otypes='d'))
            df = after_data - before_data
        else:
            data = None
            if what.name == self.steps[end].frm[1].name:
                data = self.steps[end].frm[1][:].get_dataframe()
            elif what.name == self.steps[end].to[1].name:
                data = self.steps[end].to[1][:].get_dataframe()
            df = data.applymap(numpy.vectorize(helper, cache=True, otypes='d'))

        precision = config.precisions[unit] if unit in config.precisions else config.precisions['default']
        df = df.round(precision)
        vmin, vmax = df.min().min(), df.max().max()
        styler = df.style.format(precision=precision).background_gradient(cmap, vmin=vmin, vmax=vmax)
        return styler