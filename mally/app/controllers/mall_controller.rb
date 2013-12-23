class MallController < ApplicationController

	def index
		@mall =  Mall.all
		p "==================="
		p @mall
	end

	def new
			p params.class
	end

	def show

	end
end
